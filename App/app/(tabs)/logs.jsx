import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    SafeAreaView,
    StatusBar,
    FlatList,
    RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useUser } from '../../hooks/auth_context';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { colors, gradients, typography, spacing, borderRadius, shadows, glassmorphism } from '../../theme';
import { NutritionAPI, WaterAPI, SymptomsAPI } from '../../services/apiService';

const TABS = ['Meals', 'Water', 'Symptoms'];

export default function Logs() {
    const router = useRouter();
    const { user } = useUser();
    const [activeTab, setActiveTab] = useState('Meals');
    const [meals, setMeals] = useState([]);
    const [waterLogs, setWaterLogs] = useState([]);
    const [symptoms, setSymptoms] = useState([]);
    const [refreshing, setRefreshing] = useState(false);
    const [loading, setLoading] = useState(true);

    const userId = user?.uid;

    useEffect(() => {
        if (userId) {
            loadData();
        }
    }, [userId, activeTab]);

    const loadData = async () => {
        setLoading(true);
        try {
            switch (activeTab) {
                case 'Meals':
                    const mealsData = await NutritionAPI.getAllMeals(userId, { limit: 20 });
                    setMeals(mealsData || []);
                    break;
                case 'Water':
                    const waterData = await WaterAPI.getAllWaterLogs(userId, { limit: 20 });
                    setWaterLogs(waterData || []);
                    break;
                case 'Symptoms':
                    const symptomsData = await SymptomsAPI.getRecentSymptoms(userId, { days: 7 });
                    setSymptoms(symptomsData || []);
                    break;
            }
        } catch (err) {
            console.log('Failed to load data:', err.message);
        } finally {
            setLoading(false);
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await loadData();
        setRefreshing(false);
    };

    const getAddRoute = () => {
        switch (activeTab) {
            case 'Meals':
                return '/meal-log';
            case 'Water':
                return '/water-log';
            case 'Symptoms':
                return '/symptom-log';
            default:
                return '/meal-log';
        }
    };

    const renderMealItem = ({ item }) => (
        <Card style={styles.listItem}>
            <View style={styles.itemHeader}>
                <Ionicons name="restaurant" size={24} color={colors.neonPurple} />
                <View style={styles.itemInfo}>
                    <Text style={styles.itemTitle}>{item.name}</Text>
                    <Text style={styles.itemSubtitle}>{item.amnt}g</Text>
                </View>
            </View>
            {item.analysis && (
                <View style={styles.nutrients}>
                    <Text style={styles.nutrientText}>Protein: {item.analysis.protein?.toFixed(1)}g</Text>
                    <Text style={styles.nutrientText}>Fiber: {item.analysis.fiber?.toFixed(1)}g</Text>
                </View>
            )}
        </Card>
    );

    const renderWaterItem = ({ item }) => (
        <Card style={styles.listItem}>
            <View style={styles.itemHeader}>
                <Ionicons name="water" size={24} color={colors.softBlue} />
                <View style={styles.itemInfo}>
                    <Text style={styles.itemTitle}>{item.amount_ml} ml</Text>
                    <Text style={styles.itemSubtitle}>{item.note || 'Water intake'}</Text>
                </View>
            </View>
        </Card>
    );

    const renderSymptomItem = ({ item }) => (
        <Card style={styles.listItem}>
            <View style={styles.itemHeader}>
                <Ionicons name="medical" size={24} color={colors.mutedLavender} />
                <View style={styles.itemInfo}>
                    <Text style={styles.itemTitle}>{item.symptom_name}</Text>
                    <Text style={styles.itemSubtitle}>Severity: {item.severity}/5</Text>
                </View>
            </View>
            {item.description && (
                <Text style={styles.itemDescription}>{item.description}</Text>
            )}
        </Card>
    );

    const getData = () => {
        switch (activeTab) {
            case 'Meals':
                return meals;
            case 'Water':
                return waterLogs;
            case 'Symptoms':
                return symptoms;
            default:
                return [];
        }
    };

    const renderItem = (props) => {
        switch (activeTab) {
            case 'Meals':
                return renderMealItem(props);
            case 'Water':
                return renderWaterItem(props);
            case 'Symptoms':
                return renderSymptomItem(props);
            default:
                return null;
        }
    };

    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <SafeAreaView style={styles.safeArea}>
                <View style={styles.header}>
                    <Text style={styles.title}>Your Logs</Text>
                </View>

                {/* Tab Switcher */}
                <View style={styles.tabs}>
                    {TABS.map((tab) => (
                        <TouchableOpacity
                            key={tab}
                            style={[styles.tab, activeTab === tab && styles.activeTab]}
                            onPress={() => setActiveTab(tab)}
                        >
                            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
                                {tab}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* List */}
                <FlatList
                    data={getData()}
                    renderItem={renderItem}
                    keyExtractor={(item) => item._id || item.id || Math.random().toString()}
                    contentContainerStyle={styles.listContent}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.neonPurple} />
                    }
                    ListEmptyComponent={
                        <View style={styles.empty}>
                            <Ionicons
                                name={activeTab === 'Meals' ? 'restaurant-outline' : activeTab === 'Water' ? 'water-outline' : 'medical-outline'}
                                size={48}
                                color={colors.dustyPurple}
                            />
                            <Text style={styles.emptyText}>No {activeTab.toLowerCase()} logged yet</Text>
                            <Button
                                title={`Add ${activeTab.slice(0, -1)}`}
                                onPress={() => router.push(getAddRoute())}
                                size="small"
                                style={{ marginTop: spacing.md }}
                            />
                        </View>
                    }
                />

                {/* FAB */}
                <TouchableOpacity
                    style={styles.fab}
                    onPress={() => router.push(getAddRoute())}
                >
                    <LinearGradient
                        colors={[colors.neonPurple, colors.mutedLavender]}
                        style={styles.fabGradient}
                    >
                        <Ionicons name="add" size={28} color={colors.white} />
                    </LinearGradient>
                </TouchableOpacity>

                {/* Spacer for tab bar */}
                <View style={{ height: 90 }} />
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
    header: {
        padding: spacing.lg,
        paddingBottom: spacing.md,
    },
    title: {
        ...typography.h1,
    },
    tabs: {
        flexDirection: 'row',
        paddingHorizontal: spacing.lg,
        marginBottom: spacing.md,
        gap: spacing.sm,
    },
    tab: {
        flex: 1,
        paddingVertical: spacing.sm,
        paddingHorizontal: spacing.md,
        borderRadius: borderRadius.md,
        backgroundColor: 'rgba(254, 253, 254, 0.6)',
        alignItems: 'center',
    },
    activeTab: {
        backgroundColor: colors.neonPurple,
    },
    tabText: {
        ...typography.body,
        fontWeight: '600',
        color: colors.mutedPurple,
    },
    activeTabText: {
        color: colors.white,
    },
    listContent: {
        padding: spacing.lg,
        paddingTop: 0,
        gap: spacing.md,
    },
    listItem: {
        marginBottom: spacing.sm,
    },
    itemHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.md,
    },
    itemInfo: {
        flex: 1,
    },
    itemTitle: {
        ...typography.h3,
    },
    itemSubtitle: {
        ...typography.bodySmall,
    },
    itemDescription: {
        ...typography.bodySmall,
        marginTop: spacing.sm,
        fontStyle: 'italic',
    },
    nutrients: {
        flexDirection: 'row',
        gap: spacing.md,
        marginTop: spacing.sm,
    },
    nutrientText: {
        ...typography.caption,
        backgroundColor: colors.lightOrchid,
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.sm,
    },
    empty: {
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: spacing.xxl,
    },
    emptyText: {
        ...typography.body,
        color: colors.dustyPurple,
        marginTop: spacing.md,
    },
    fab: {
        position: 'absolute',
        right: spacing.lg,
        bottom: 110,
        ...shadows.glow,
    },
    fabGradient: {
        width: 56,
        height: 56,
        borderRadius: 28,
        justifyContent: 'center',
        alignItems: 'center',
    },
});
