import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    SafeAreaView,
    StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useUser } from '../../hooks/auth_context';
import Card from '../../components/Card';
import { colors, gradients, typography, spacing, borderRadius, shadows, glassmorphism } from '../../theme';
import { InsightsAPI } from '../../services/apiService';

const FEATURES = [
    {
        id: 'chat',
        title: 'Chat',
        icon: 'chatbubbles',
        route: '/chat',
        color: colors.neonPurple,
    },
    {
        id: 'medicstone',
        title: 'Symptom Log',
        icon: 'medical',
        route: '/symptom-log',
        color: colors.softBlue,
    },
    {
        id: 'symptoms',
        title: 'Symptom\nReport',
        icon: 'document-text',
        route: '/symptom-report',
        color: colors.mutedLavender,
    },
    {
        id: 'hospitals',
        title: 'Nearby\nHospital',
        icon: 'location',
        route: '/hospitals',
        color: colors.dustyPurple,
    },
    {
        id: 'vaccines',
        title: 'Vaccine\nTracker',
        icon: 'shield-checkmark',
        route: '/vacc-tracker',
        color: colors.success,
    },
    {
        id: 'diet-planner',
        title: 'Diet\nPlanner',
        icon: 'calendar',
        route: '/diet-planner',
        color: colors.neonPurple,
    },
];

export default function Home() {
    const router = useRouter();
    const { user } = useUser();
    const [insights, setInsights] = useState(null);
    const [insightsLoading, setInsightsLoading] = useState(false);

    const displayName = user?.displayName || 'there';
    const userId = user?.uid;

    // Post-process insights to clean up nutrient names like 'iron_mg' -> 'Iron'
    const processInsights = (rawInsights) => {
        if (!rawInsights) return null;
        
        // Clean up nutrient name format: iron_mg -> Iron, vitamin_d_iu -> Vitamin D
        const formatNutrientName = (name) => {
            if (!name || typeof name !== 'string') return name;
            
            // Remove unit suffixes like _mg, _g, _iu, _mcg
            let cleaned = name.replace(/_(mg|g|iu|mcg|µg|ml|kcal)$/i, '');
            
            // Replace underscores with spaces and capitalize
            cleaned = cleaned
                .split('_')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                .join(' ');
            
            return cleaned;
        };

        const processed = { ...rawInsights };
        
        // Process priority_nutrients array
        if (processed.priority_nutrients && Array.isArray(processed.priority_nutrients)) {
            processed.priority_nutrients = processed.priority_nutrients.map(formatNutrientName);
        }
        
        // Process current_nutrients array
        if (processed.current_nutrients && Array.isArray(processed.current_nutrients)) {
            processed.current_nutrients = processed.current_nutrients.map(nutrient => ({
                ...nutrient,
                name: formatNutrientName(nutrient.name)
            }));
        }
        
        // Process nutrient_forecasts object keys
        if (processed.nutrient_forecasts && typeof processed.nutrient_forecasts === 'object') {
            const newForecasts = {};
            for (const [key, value] of Object.entries(processed.nutrient_forecasts)) {
                newForecasts[formatNutrientName(key)] = value;
            }
            processed.nutrient_forecasts = newForecasts;
        }
        
        // Process dietary_recommendations - clean up any nutrient mentions
        if (processed.dietary_recommendations && Array.isArray(processed.dietary_recommendations)) {
            processed.dietary_recommendations = processed.dietary_recommendations.map(rec => {
                if (typeof rec !== 'string') return rec;
                // Replace patterns like "iron_mg" with "Iron"
                return rec.replace(/\b(\w+)_(mg|g|iu|mcg|µg)\b/gi, (match, name) => {
                    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
                });
            });
        }
        
        return processed;
    };

    useEffect(() => {
        if (userId) {
            loadInsights();
        }
    }, [userId]);

    const loadInsights = async () => {
        if (!userId) return;
        
        setInsightsLoading(true);
        try {
            // First try to get cached insights
            console.log('Fetching insights for user:', userId);
            const data = await InsightsAPI.getLatestInsights(userId);
            console.log('Got cached insights:', data);
            setInsights(processInsights(data?.insights));
        } catch (err) {
            // If no cached insights, try to generate new ones
            console.log('No cached insights found, generating new ones...');
            try {
                // Generate insights with default values
                const newData = await InsightsAPI.generateInsights(userId, {
                    trimester: 'trimester_2', // Default trimester
                    age: 28,
                    height_cm: 165,
                    weight_kg: 60,
                    activity_factor: 1.4,
                    forecast_days: 7,
                    context_days: 30,
                    force_regenerate: false,
                });
                console.log('Generated new insights:', newData);
                setInsights(processInsights(newData?.insights));
            } catch (genErr) {
                console.log('Failed to generate insights:', genErr.message);
                // Insights require meal data logged by the user
            }
        } finally {
            setInsightsLoading(false);
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
                        <View>
                            <Text style={styles.greeting}>Hello,</Text>
                            <Text style={styles.name}>{displayName} 👋</Text>
                        </View>
                        <TouchableOpacity
                            style={styles.profileButton}
                            onPress={() => router.push('/(tabs)/profile')}
                        >
                            <Ionicons name="person-circle" size={44} color={colors.neonPurple} />
                        </TouchableOpacity>
                    </View>

                    {/* Feature Grid */}
                    <View style={styles.grid}>
                        {FEATURES.map((feature) => (
                            <Card
                                key={feature.id}
                                style={styles.featureCard}
                                onPress={() => router.push(feature.route)}
                            >
                                <View style={[styles.iconCircle, { backgroundColor: feature.color + '20' }]}>
                                    <Ionicons name={feature.icon} size={28} color={feature.color} />
                                </View>
                                <Text style={styles.featureTitle}>{feature.title}</Text>
                            </Card>
                        ))}
                    </View>

                    {/* Insights Section */}
                    <View style={styles.insightsSection}>
                        <Text style={styles.sectionTitle}>Insights & Trends</Text>
                        <Card style={styles.insightsCard}>
                            {insightsLoading ? (
                                <View style={styles.emptyInsights}>
                                    <Ionicons name="hourglass" size={40} color={colors.neonPurple} />
                                    <Text style={styles.emptyText}>
                                        Generating your personalized insights...
                                    </Text>
                                </View>
                            ) : insights ? (
                                <View>
                                    <View style={styles.insightRow}>
                                        <Ionicons name="trending-up" size={20} color={colors.neonPurple} />
                                        <Text style={styles.insightText}>
                                            {insights.consistency_score
                                                ? `Tracking consistency: ${Math.round(insights.consistency_score)}%`
                                                : insights.tracking_consistency
                                                    ? `Tracking consistency: ${Math.round(insights.tracking_consistency * 100)}%`
                                                    : 'Keep logging to see your trends!'}
                                        </Text>
                                    </View>
                                    {insights.priority_nutrients && insights.priority_nutrients.length > 0 && (
                                        <View style={styles.insightRow}>
                                            <Ionicons name="nutrition" size={20} color={colors.softBlue} />
                                            <Text style={styles.insightText}>
                                                Focus on: {insights.priority_nutrients.slice(0, 2).join(', ')}
                                            </Text>
                                        </View>
                                    )}
                                    {insights.dietary_recommendations && insights.dietary_recommendations.length > 0 && (
                                        <View style={styles.insightRow}>
                                            <Ionicons name="bulb" size={20} color={colors.warning} />
                                            <Text style={styles.insightText}>
                                                {insights.dietary_recommendations[0]}
                                            </Text>
                                        </View>
                                    )}
                                </View>
                            ) : (
                                <View style={styles.emptyInsights}>
                                    <Ionicons name="analytics-outline" size={40} color={colors.dustyPurple} />
                                    <Text style={styles.emptyText}>
                                        Start logging meals and symptoms to see personalized insights!
                                    </Text>
                                </View>
                            )}
                        </Card>
                    </View>

                    {/* Spacer for tab bar */}
                    <View style={{ height: 100 }} />
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
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.xl,
        marginTop: spacing.md,
    },
    greeting: {
        ...typography.body,
        color: colors.mutedPurple,
    },
    name: {
        ...typography.h1,
        color: colors.inkPurple,
    },
    profileButton: {
        padding: spacing.xs,
    },
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.md,
        marginBottom: spacing.xl,
    },
    featureCard: {
        width: '47%',
        aspectRatio: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    iconCircle: {
        width: 56,
        height: 56,
        borderRadius: 28,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: spacing.sm,
    },
    featureTitle: {
        ...typography.body,
        fontWeight: '600',
        color: colors.inkPurple,
        textAlign: 'center',
    },
    sectionTitle: {
        ...typography.h2,
        marginBottom: spacing.md,
    },
    insightsSection: {
        marginBottom: spacing.lg,
    },
    insightsCard: {
        padding: spacing.lg,
    },
    insightRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        marginBottom: spacing.sm,
    },
    insightText: {
        ...typography.body,
        flex: 1,
    },
    emptyInsights: {
        alignItems: 'center',
        padding: spacing.md,
    },
    emptyText: {
        ...typography.body,
        textAlign: 'center',
        marginTop: spacing.sm,
        color: colors.dustyPurple,
    },
});