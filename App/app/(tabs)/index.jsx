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
        title: 'MedicStone',
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
];

export default function Home() {
    const router = useRouter();
    const { user } = useUser();
    const [insights, setInsights] = useState(null);

    const displayName = user?.displayName || 'there';
    const userId = user?.uid;

    useEffect(() => {
        if (userId) {
            loadInsights();
        }
    }, [userId]);

    const loadInsights = async () => {
        try {
            const data = await InsightsAPI.getLatestInsights(userId);
            setInsights(data?.insights);
        } catch (err) {
            // Silently fail - insights are optional
            console.log('No insights available');
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
                            {insights ? (
                                <View>
                                    <View style={styles.insightRow}>
                                        <Ionicons name="trending-up" size={20} color={colors.neonPurple} />
                                        <Text style={styles.insightText}>
                                            {insights.tracking_consistency
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