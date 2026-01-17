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

import { useUser } from '../hooks/auth_context';
import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';
import { SymptomsAPI, MemoryAPI } from '../services/apiService';

export default function SymptomReport() {
    const router = useRouter();
    const { user } = useUser();

    const [frequencies, setFrequencies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generatingSummary, setGeneratingSummary] = useState(false);

    const userId = user?.uid;

    useEffect(() => {
        if (userId) {
            loadData();
        }
    }, [userId]);

    const loadData = async () => {
        setLoading(true);
        try {
            const data = await SymptomsAPI.getAllFrequencies(userId, 30);
            setFrequencies(data || []);
        } catch (err) {
            console.log('Failed to load symptom frequencies');
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateSummary = async () => {
        if (!userId || generatingSummary) return;
        
        setGeneratingSummary(true);
        try {
            const summary = await MemoryAPI.getDoctorSummary(userId, { days: 30, format: 'json' });
            // Navigate to summary view with the data
            router.push({
                pathname: '/doctor-summary',
                params: { summary: JSON.stringify(summary) }
            });
        } catch (err) {
            console.log('Failed to generate doctor summary:', err);
            alert('Failed to generate doctor summary. Please try again.');
        } finally {
            setGeneratingSummary(false);
        }
    };

    const getSeverityColor = (severity) => {
        if (severity <= 2) return colors.success;
        if (severity <= 3) return colors.warning;
        return colors.error;
    };

    const getTrendIcon = (trend) => {
        switch (trend) {
            case 'increasing':
                return { name: 'trending-up', color: colors.error };
            case 'decreasing':
                return { name: 'trending-down', color: colors.success };
            default:
                return { name: 'remove', color: colors.dustyPurple };
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
                        <Text style={styles.title}>Symptom Report</Text>
                        <View style={{ width: 40 }} />
                    </View>

                    {/* Period Info */}
                    <View style={styles.periodBanner}>
                        <Ionicons name="calendar-outline" size={20} color={colors.neonPurple} />
                        <Text style={styles.periodText}>Last 30 days analysis</Text>
                    </View>

                    {/* Frequency Cards */}
                    {loading ? (
                        <Card style={styles.loadingCard}>
                            <Text style={styles.loadingText}>Loading symptom data...</Text>
                        </Card>
                    ) : frequencies.length === 0 ? (
                        <Card style={styles.emptyCard}>
                            <Ionicons name="analytics-outline" size={48} color={colors.dustyPurple} />
                            <Text style={styles.emptyTitle}>No Symptoms Recorded</Text>
                            <Text style={styles.emptyText}>
                                Start logging symptoms to see your health patterns and trends.
                            </Text>
                            <TouchableOpacity
                                style={styles.logButton}
                                onPress={() => router.push('/symptom-log')}
                            >
                                <Text style={styles.logButtonText}>Log a Symptom</Text>
                            </TouchableOpacity>
                        </Card>
                    ) : (
                        frequencies.map((freq, index) => {
                            const trendInfo = getTrendIcon(freq.trend || freq.severity_trend);
                            return (
                                <Card key={index} style={styles.frequencyCard}>
                                    <View style={styles.frequencyHeader}>
                                        <View style={styles.symptomName}>
                                            <View style={[styles.dot, { backgroundColor: getSeverityColor(freq.avg_severity || freq.avgSeverity) }]} />
                                            <Text style={styles.symptomTitle}>
                                                {freq.symptom_name || freq.name}
                                            </Text>
                                        </View>
                                        <View style={styles.trendBadge}>
                                            <Ionicons name={trendInfo.name} size={16} color={trendInfo.color} />
                                        </View>
                                    </View>

                                    <View style={styles.statsRow}>
                                        <View style={styles.stat}>
                                            <Text style={styles.statValue}>
                                                {freq.total_occurrences || freq.occurrences || 0}
                                            </Text>
                                            <Text style={styles.statLabel}>Occurrences</Text>
                                        </View>
                                        <View style={styles.stat}>
                                            <Text style={styles.statValue}>
                                                {(freq.avg_severity || freq.avgSeverity || 0).toFixed(1)}
                                            </Text>
                                            <Text style={styles.statLabel}>Avg Severity</Text>
                                        </View>
                                        <View style={styles.stat}>
                                            <Text style={styles.statValue}>
                                                {(freq.frequency_per_week || freq.weekly_frequency || 0).toFixed(1)}
                                            </Text>
                                            <Text style={styles.statLabel}>Per Week</Text>
                                        </View>
                                    </View>
                                </Card>
                            );
                        })
                    )}

                    {/* Doctor Summary Button */}
                    {frequencies.length > 0 && (
                        <TouchableOpacity 
                            style={styles.summaryButton}
                            onPress={handleGenerateSummary}
                            disabled={generatingSummary}
                        >
                            <LinearGradient
                                colors={generatingSummary ? [colors.dustyPurple, colors.lightOrchid] : [colors.neonPurple, colors.mutedLavender]}
                                start={{ x: 0, y: 0 }}
                                end={{ x: 1, y: 0 }}
                                style={styles.summaryButtonGradient}
                            >
                                <Ionicons 
                                    name={generatingSummary ? "hourglass" : "document-text"} 
                                    size={20} 
                                    color={colors.white} 
                                />
                                <Text style={styles.summaryButtonText}>
                                    {generatingSummary ? 'Generating...' : 'Generate Doctor Summary'}
                                </Text>
                            </LinearGradient>
                        </TouchableOpacity>
                    )}
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
        paddingBottom: spacing.xxl,
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
    title: {
        ...typography.h2,
    },
    periodBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        backgroundColor: colors.neonPurple + '15',
        padding: spacing.md,
        borderRadius: borderRadius.md,
        marginBottom: spacing.lg,
    },
    periodText: {
        ...typography.body,
        color: colors.inkPurple,
    },
    loadingCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    loadingText: {
        ...typography.body,
        color: colors.dustyPurple,
    },
    emptyCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    emptyTitle: {
        ...typography.h3,
        marginTop: spacing.md,
        marginBottom: spacing.sm,
    },
    emptyText: {
        ...typography.body,
        color: colors.dustyPurple,
        textAlign: 'center',
    },
    logButton: {
        marginTop: spacing.lg,
        backgroundColor: colors.neonPurple,
        paddingVertical: spacing.sm,
        paddingHorizontal: spacing.lg,
        borderRadius: borderRadius.md,
    },
    logButtonText: {
        ...typography.button,
    },
    frequencyCard: {
        marginBottom: spacing.md,
        padding: spacing.lg,
    },
    frequencyHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    symptomName: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
    },
    dot: {
        width: 12,
        height: 12,
        borderRadius: 6,
    },
    symptomTitle: {
        ...typography.h3,
        textTransform: 'capitalize',
    },
    trendBadge: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: colors.lightOrchid,
        justifyContent: 'center',
        alignItems: 'center',
    },
    statsRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
    },
    stat: {
        alignItems: 'center',
    },
    statValue: {
        ...typography.h2,
        color: colors.neonPurple,
    },
    statLabel: {
        ...typography.caption,
        marginTop: spacing.xs,
    },
    summaryButton: {
        marginTop: spacing.lg,
        ...shadows.glow,
    },
    summaryButtonGradient: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: spacing.sm,
        padding: spacing.md,
        borderRadius: borderRadius.md,
    },
    summaryButtonText: {
        ...typography.button,
    },
});
