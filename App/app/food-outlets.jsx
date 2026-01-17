import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    SafeAreaView,
    StatusBar,
    Linking,
    Platform,
    Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';

import { useUser } from '../hooks/auth_context';
import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';
import { FoodOutletAPI, InsightsAPI } from '../services/apiService';

const CATEGORIES = [
    { id: 'all', label: 'All', icon: 'restaurant' },
    { id: 'restaurant', label: 'Restaurant', icon: 'restaurant-outline' },
    { id: 'grocery', label: 'Grocery', icon: 'cart-outline' },
    { id: 'organic', label: 'Organic', icon: 'leaf-outline' },
    { id: 'cafe', label: 'Cafe', icon: 'cafe-outline' },
];

export default function FoodOutlets() {
    const router = useRouter();
    const { user } = useUser();

    const [outlets, setOutlets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [location, setLocation] = useState(null);
    const [priorityNutrients, setPriorityNutrients] = useState(null);
    const [nutrientTips, setNutrientTips] = useState(null);

    const userId = user?.uid;

    useEffect(() => {
        initializeData();
    }, [userId]);

    useEffect(() => {
        if (location) {
            loadOutlets();
        }
    }, [location, selectedCategory]);

    const initializeData = async () => {
        // Get user's location
        try {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                setError('Location permission is required to find nearby food outlets');
                setLoading(false);
                return;
            }

            const loc = await Location.getCurrentPositionAsync({});
            setLocation({
                lat: loc.coords.latitude,
                lng: loc.coords.longitude,
            });
        } catch (err) {
            setError('Failed to get your location');
            setLoading(false);
            return;
        }

        // Try to get priority nutrients from insights
        if (userId) {
            try {
                const insights = await InsightsAPI.getLatestInsights(userId);
                if (insights?.insights?.priority_nutrients) {
                    // Clean nutrient names
                    const cleaned = insights.insights.priority_nutrients.map(n => 
                        n.replace(/_(mg|g|iu|mcg)$/i, '')
                    );
                    setPriorityNutrients(cleaned);
                }
            } catch (err) {
                // No insights available, that's okay
                console.log('No insights for food recommendations');
            }
        }
    };

    const loadOutlets = async () => {
        if (!location) return;

        setLoading(true);
        setError(null);

        try {
            const data = await FoodOutletAPI.findNearbyOutlets({
                lat: location.lat,
                lng: location.lng,
                radius: 3000,
                limit: 15,
                category: selectedCategory,
                priority_nutrients: priorityNutrients,
            });

            setOutlets(data.outlets || []);
            if (data.nutrient_recommendations) {
                setNutrientTips(data.nutrient_recommendations);
            }
        } catch (err) {
            console.log('Failed to load outlets:', err);
            setError('Failed to find nearby food outlets');
        } finally {
            setLoading(false);
        }
    };

    const openMaps = (outlet) => {
        const { lat, lng } = outlet.location;
        const label = encodeURIComponent(outlet.name);
        
        const url = Platform.select({
            ios: `maps:0,0?q=${label}@${lat},${lng}`,
            android: `geo:0,0?q=${lat},${lng}(${label})`,
        });

        Linking.canOpenURL(url).then(supported => {
            if (supported) {
                Linking.openURL(url);
            } else {
                // Fallback to Google Maps web
                Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${lat},${lng}`);
            }
        });
    };

    const getCategoryIcon = (category) => {
        switch (category) {
            case 'grocery':
                return 'cart';
            case 'cafe':
                return 'cafe';
            case 'bakery':
                return 'pizza';
            case 'organic':
                return 'leaf';
            default:
                return 'restaurant';
        }
    };

    const getCategoryColor = (category) => {
        switch (category) {
            case 'grocery':
                return colors.softBlue;
            case 'cafe':
                return colors.warning;
            case 'organic':
                return colors.success;
            case 'bakery':
                return colors.dustyPurple;
            default:
                return colors.neonPurple;
        }
    };

    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <SafeAreaView style={styles.safeArea}>
                <ScrollView
                    style={styles.scrollView}
                    contentContainerStyle={styles.scrollContent}
                    showsVerticalScrollIndicator={false}
                >
                    {/* Header */}
                    <View style={styles.header}>
                        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                            <Ionicons name="arrow-back" size={24} color={colors.inkPurple} />
                        </TouchableOpacity>
                        <Text style={styles.title}>Healthy Food</Text>
                        <TouchableOpacity onPress={loadOutlets} style={styles.refreshButton}>
                            <Ionicons name="refresh" size={24} color={colors.neonPurple} />
                        </TouchableOpacity>
                    </View>

                    {/* Category Filters */}
                    <ScrollView
                        horizontal
                        showsHorizontalScrollIndicator={false}
                        style={styles.categoriesScroll}
                        contentContainerStyle={styles.categoriesContent}
                    >
                        {CATEGORIES.map(cat => (
                            <TouchableOpacity
                                key={cat.id}
                                style={[
                                    styles.categoryChip,
                                    selectedCategory === cat.id && styles.categoryChipActive
                                ]}
                                onPress={() => setSelectedCategory(cat.id)}
                            >
                                <Ionicons
                                    name={cat.icon}
                                    size={16}
                                    color={selectedCategory === cat.id ? colors.white : colors.neonPurple}
                                />
                                <Text style={[
                                    styles.categoryText,
                                    selectedCategory === cat.id && styles.categoryTextActive
                                ]}>
                                    {cat.label}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </ScrollView>

                    {/* Nutrient Tips Banner */}
                    {priorityNutrients && priorityNutrients.length > 0 && (
                        <Card style={styles.tipsBanner}>
                            <View style={styles.tipsHeader}>
                                <Ionicons name="bulb" size={20} color={colors.warning} />
                                <Text style={styles.tipsTitle}>Based on your nutrition needs</Text>
                            </View>
                            <Text style={styles.tipsText}>
                                Looking for places with foods rich in: {priorityNutrients.slice(0, 3).join(', ')}
                            </Text>
                        </Card>
                    )}

                    {/* Loading State */}
                    {loading && (
                        <Card style={styles.loadingCard}>
                            <Ionicons name="restaurant" size={40} color={colors.dustyPurple} />
                            <Text style={styles.loadingText}>Finding healthy food options nearby...</Text>
                        </Card>
                    )}

                    {/* Error State */}
                    {error && !loading && (
                        <Card style={styles.errorCard}>
                            <Ionicons name="alert-circle" size={40} color={colors.error} />
                            <Text style={styles.errorText}>{error}</Text>
                            <TouchableOpacity style={styles.retryButton} onPress={initializeData}>
                                <Text style={styles.retryText}>Try Again</Text>
                            </TouchableOpacity>
                        </Card>
                    )}

                    {/* Outlets List */}
                    {!loading && !error && outlets.length === 0 && (
                        <Card style={styles.emptyCard}>
                            <Ionicons name="search" size={40} color={colors.dustyPurple} />
                            <Text style={styles.emptyTitle}>No outlets found</Text>
                            <Text style={styles.emptyText}>
                                Try expanding your search or changing the category
                            </Text>
                        </Card>
                    )}

                    {!loading && !error && outlets.map((outlet, index) => (
                        <TouchableOpacity
                            key={index}
                            activeOpacity={0.8}
                            onPress={() => openMaps(outlet)}
                        >
                            <Card style={styles.outletCard}>
                                <View style={styles.outletHeader}>
                                    <View style={[
                                        styles.outletIcon,
                                        { backgroundColor: getCategoryColor(outlet.category) + '20' }
                                    ]}>
                                        <Ionicons
                                            name={getCategoryIcon(outlet.category)}
                                            size={24}
                                            color={getCategoryColor(outlet.category)}
                                        />
                                    </View>
                                    <View style={styles.outletInfo}>
                                        <Text style={styles.outletName}>{outlet.name}</Text>
                                        <Text style={styles.outletCategory}>
                                            {outlet.category.charAt(0).toUpperCase() + outlet.category.slice(1)}
                                        </Text>
                                    </View>
                                    <Ionicons name="navigate" size={20} color={colors.neonPurple} />
                                </View>

                                <Text style={styles.outletAddress}>{outlet.address}</Text>

                                {outlet.distance_meters && (
                                    <View style={styles.distanceBadge}>
                                        <Ionicons name="location" size={14} color={colors.dustyPurple} />
                                        <Text style={styles.distanceText}>
                                            {outlet.distance_meters < 1000
                                                ? `${Math.round(outlet.distance_meters)}m away`
                                                : `${(outlet.distance_meters / 1000).toFixed(1)}km away`}
                                        </Text>
                                    </View>
                                )}

                                {outlet.nutrient_match && outlet.nutrient_match.length > 0 && (
                                    <View style={styles.nutrientMatch}>
                                        <Ionicons name="nutrition" size={14} color={colors.success} />
                                        <Text style={styles.nutrientMatchText}>
                                            {outlet.recommendation || `Good for: ${outlet.nutrient_match.join(', ')}`}
                                        </Text>
                                    </View>
                                )}
                            </Card>
                        </TouchableOpacity>
                    ))}

                    {/* Bottom spacer */}
                    <View style={{ height: spacing.xxl }} />
                </ScrollView>
            </SafeAreaView>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    safeArea: {
        flex: 1,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: spacing.lg,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: spacing.lg,
        marginTop: spacing.md,
    },
    backButton: {
        padding: spacing.sm,
    },
    refreshButton: {
        padding: spacing.sm,
    },
    title: {
        ...typography.h2,
    },
    categoriesScroll: {
        marginBottom: spacing.lg,
    },
    categoriesContent: {
        gap: spacing.sm,
    },
    categoryChip: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.full,
        backgroundColor: colors.white,
        borderWidth: 1,
        borderColor: colors.lightOrchid,
    },
    categoryChipActive: {
        backgroundColor: colors.neonPurple,
        borderColor: colors.neonPurple,
    },
    categoryText: {
        ...typography.bodySmall,
        color: colors.neonPurple,
    },
    categoryTextActive: {
        color: colors.white,
    },
    tipsBanner: {
        padding: spacing.md,
        marginBottom: spacing.lg,
        backgroundColor: colors.warning + '10',
        borderColor: colors.warning + '30',
    },
    tipsHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        marginBottom: spacing.xs,
    },
    tipsTitle: {
        ...typography.bodySmall,
        fontWeight: '600',
        color: colors.inkPurple,
    },
    tipsText: {
        ...typography.caption,
        color: colors.mutedPurple,
    },
    loadingCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    loadingText: {
        ...typography.body,
        color: colors.dustyPurple,
        marginTop: spacing.md,
        textAlign: 'center',
    },
    errorCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    errorText: {
        ...typography.body,
        color: colors.error,
        marginTop: spacing.md,
        textAlign: 'center',
    },
    retryButton: {
        marginTop: spacing.md,
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.sm,
        backgroundColor: colors.neonPurple,
        borderRadius: borderRadius.md,
    },
    retryText: {
        ...typography.button,
    },
    emptyCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    emptyTitle: {
        ...typography.h3,
        marginTop: spacing.md,
    },
    emptyText: {
        ...typography.body,
        color: colors.dustyPurple,
        textAlign: 'center',
        marginTop: spacing.sm,
    },
    outletCard: {
        padding: spacing.lg,
        marginBottom: spacing.md,
    },
    outletHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: spacing.sm,
    },
    outletIcon: {
        width: 44,
        height: 44,
        borderRadius: 22,
        justifyContent: 'center',
        alignItems: 'center',
    },
    outletInfo: {
        flex: 1,
        marginLeft: spacing.md,
    },
    outletName: {
        ...typography.h3,
    },
    outletCategory: {
        ...typography.caption,
    },
    outletAddress: {
        ...typography.bodySmall,
        color: colors.mutedPurple,
        marginBottom: spacing.sm,
    },
    distanceBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        marginBottom: spacing.sm,
    },
    distanceText: {
        ...typography.caption,
    },
    nutrientMatch: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        backgroundColor: colors.success + '15',
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.sm,
        alignSelf: 'flex-start',
    },
    nutrientMatchText: {
        ...typography.caption,
        color: colors.success,
        fontWeight: '500',
    },
});
