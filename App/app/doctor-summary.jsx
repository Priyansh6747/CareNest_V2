import React, { useMemo } from 'react';
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
import { useRouter, useLocalSearchParams } from 'expo-router';

import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius } from '../theme';

export default function DoctorSummary() {
    const router = useRouter();
    const { summary: summaryParam } = useLocalSearchParams();

    const summary = useMemo(() => {
        if (!summaryParam) return null;
        try {
            return JSON.parse(summaryParam);
        } catch {
            return null;
        }
    }, [summaryParam]);

    if (!summary) {
        return (
            <LinearGradient colors={gradients.background} style={styles.container}>
                <SafeAreaView style={styles.safeArea}>
                    <View style={styles.errorContainer}>
                        <Ionicons name="alert-circle" size={48} color={colors.error} />
                        <Text style={styles.errorText}>Failed to load summary</Text>
                        <TouchableOpacity onPress={() => router.back()} style={styles.backLink}>
                            <Text style={styles.backLinkText}>Go Back</Text>
                        </TouchableOpacity>
                    </View>
                </SafeAreaView>
            </LinearGradient>
        );
    }

    const getSeverityColor = (severity) => {
        if (severity <= 2) return colors.success;
        if (severity <= 3) return colors.warning;
        return colors.error;
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
                        <Text style={styles.title}>Doctor Summary</Text>
                        <View style={{ width: 40 }} />
                    </View>

                    {/* Period Info */}
                    <Card style={styles.infoCard}>
                        <View style={styles.infoRow}>
                            <Ionicons name="calendar" size={20} color={colors.neonPurple} />
                            <Text style={styles.infoText}>
                                Period: {summary.period_days || 30} days
                            </Text>
                        </View>
                        <View style={styles.infoRow}>
                            <Ionicons name="time" size={20} color={colors.neonPurple} />
                            <Text style={styles.infoText}>
                                Generated: {new Date().toLocaleDateString()}
                            </Text>
                        </View>
                    </Card>

                    {/* Summary Overview */}
                    {summary.overview && (
                        <Card style={styles.overviewCard}>
                            <Text style={styles.sectionTitle}>Overview</Text>
                            <Text style={styles.overviewText}>{summary.overview}</Text>
                        </Card>
                    )}

                    {/* Symptom Frequencies */}
                    {summary.symptom_frequencies && summary.symptom_frequencies.length > 0 && (
                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}>Symptom Frequencies</Text>
                            {summary.symptom_frequencies.map((freq, index) => (
                                <Card key={index} style={styles.symptomCard}>
                                    <View style={styles.symptomHeader}>
                                        <View style={[styles.dot, { backgroundColor: getSeverityColor(freq.avg_severity) }]} />
                                        <Text style={styles.symptomName}>{freq.symptom_name}</Text>
                                    </View>
                                    <View style={styles.statsRow}>
                                        <View style={styles.stat}>
                                            <Text style={styles.statValue}>{freq.total_occurrences}</Text>
                                            <Text style={styles.statLabel}>Occurrences</Text>
                                        </View>
                                        <View style={styles.stat}>
                                            <Text style={styles.statValue}>{freq.avg_severity?.toFixed(1)}</Text>
                                            <Text style={styles.statLabel}>Avg Severity</Text>
                                        </View>
                                    </View>
                                </Card>
                            ))}
                        </View>
                    )}

                    {/* Patterns */}
                    {summary.patterns && summary.patterns.length > 0 && (
                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}>Detected Patterns</Text>
                            <Card style={styles.patternsCard}>
                                {summary.patterns.map((pattern, index) => (
                                    <View key={index} style={styles.patternItem}>
                                        <Ionicons name="analytics" size={16} color={colors.neonPurple} />
                                        <Text style={styles.patternText}>{pattern}</Text>
                                    </View>
                                ))}
                            </Card>
                        </View>
                    )}

                    {/* Recommendations */}
                    {summary.recommendations && summary.recommendations.length > 0 && (
                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}>Recommendations</Text>
                            <Card style={styles.recommendationsCard}>
                                {summary.recommendations.map((rec, index) => (
                                    <View key={index} style={styles.recItem}>
                                        <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                                        <Text style={styles.recText}>{rec}</Text>
                                    </View>
                                ))}
                            </Card>
                        </View>
                    )}

                    {/* Raw Data (Debug/Fallback) */}
                    {!summary.symptom_frequencies && !summary.patterns && (
                        <Card style={styles.rawCard}>
                            <Text style={styles.sectionTitle}>Report Data</Text>
                            <Text style={styles.rawText}>
                                {JSON.stringify(summary, null, 2)}
                            </Text>
                        </Card>
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
    errorContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: spacing.xl,
    },
    errorText: {
        ...typography.h3,
        color: colors.error,
        marginTop: spacing.md,
    },
    backLink: {
        marginTop: spacing.lg,
    },
    backLinkText: {
        ...typography.body,
        color: colors.neonPurple,
    },
    infoCard: {
        padding: spacing.lg,
        marginBottom: spacing.lg,
    },
    infoRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        marginBottom: spacing.sm,
    },
    infoText: {
        ...typography.body,
    },
    overviewCard: {
        padding: spacing.lg,
        marginBottom: spacing.lg,
    },
    overviewText: {
        ...typography.body,
        marginTop: spacing.sm,
        lineHeight: 22,
    },
    section: {
        marginBottom: spacing.lg,
    },
    sectionTitle: {
        ...typography.h3,
        marginBottom: spacing.md,
    },
    symptomCard: {
        padding: spacing.md,
        marginBottom: spacing.sm,
    },
    symptomHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        marginBottom: spacing.sm,
    },
    dot: {
        width: 10,
        height: 10,
        borderRadius: 5,
    },
    symptomName: {
        ...typography.body,
        fontWeight: '600',
        textTransform: 'capitalize',
    },
    statsRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
    },
    stat: {
        alignItems: 'center',
    },
    statValue: {
        ...typography.h3,
        color: colors.neonPurple,
    },
    statLabel: {
        ...typography.caption,
    },
    patternsCard: {
        padding: spacing.lg,
    },
    patternItem: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: spacing.sm,
        marginBottom: spacing.sm,
    },
    patternText: {
        ...typography.body,
        flex: 1,
    },
    recommendationsCard: {
        padding: spacing.lg,
    },
    recItem: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: spacing.sm,
        marginBottom: spacing.sm,
    },
    recText: {
        ...typography.body,
        flex: 1,
    },
    rawCard: {
        padding: spacing.lg,
    },
    rawText: {
        ...typography.caption,
        fontFamily: 'monospace',
        marginTop: spacing.sm,
    },
});
