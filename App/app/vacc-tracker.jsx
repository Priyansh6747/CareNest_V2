import React, { useState } from 'react';
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

import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';
import Vaccines from '../constants/Vaccines';

export default function VaccTracker() {
    const router = useRouter();
    
    // State to track checked vaccines
    const [checkedVaccines, setCheckedVaccines] = useState({});

    // Format age labels for better display
    const formatAgeLabel = (age) => {
        switch (age) {
            case '16_18 Months':
                return '16-18 Months';
            case '4_6 Years':
                return '4-6 Years';
            case '10_12 Years':
                return '10-12 Years';
            default:
                return age;
        }
    };

    // Handle checkbox change
    const handleVaccineCheck = (ageGroup, vaccineIndex, isChecked) => {
        const key = `${ageGroup}_${vaccineIndex}`;
        setCheckedVaccines(prev => ({
            ...prev,
            [key]: isChecked
        }));
    };

    // Check if a vaccine is checked
    const isVaccineChecked = (ageGroup, vaccineIndex) => {
        const key = `${ageGroup}_${vaccineIndex}`;
        return checkedVaccines[key] || false;
    };

    // Convert vaccine object to array with formatted age labels
    const vaccineEntries = Object.entries(Vaccines).map(([age, vaccines]) => ({
        age: formatAgeLabel(age),
        originalAge: age,
        vaccines: vaccines
    }));

    // Calculate completion percentage for an age group
    const getCompletionPercentage = (ageGroup, vaccines) => {
        const totalVaccines = vaccines.length;
        const checkedCount = vaccines.filter((_, index) =>
            isVaccineChecked(ageGroup, index)
        ).length;
        return totalVaccines > 0 ? Math.round((checkedCount / totalVaccines) * 100) : 0;
    };

    // Calculate overall progress
    const getOverallProgress = () => {
        let total = 0;
        let checked = 0;
        vaccineEntries.forEach(entry => {
            total += entry.vaccines.length;
            entry.vaccines.forEach((_, index) => {
                if (isVaccineChecked(entry.originalAge, index)) {
                    checked++;
                }
            });
        });
        return total > 0 ? Math.round((checked / total) * 100) : 0;
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
                        <Text style={styles.title}>Vaccine Tracker</Text>
                        <View style={{ width: 40 }} />
                    </View>

                    {/* Overall Progress Card */}
                    <Card style={styles.overallCard}>
                        <View style={styles.overallHeader}>
                            <LinearGradient
                                colors={[colors.neonPurple, colors.mutedLavender]}
                                style={styles.iconCircle}
                            >
                                <Ionicons name="medical" size={24} color={colors.white} />
                            </LinearGradient>
                            <View style={styles.overallInfo}>
                                <Text style={styles.overallTitle}>Overall Progress</Text>
                                <Text style={styles.overallSubtitle}>Track your baby's vaccinations</Text>
                            </View>
                            <View style={styles.overallBadge}>
                                <Text style={styles.overallPercentage}>{getOverallProgress()}%</Text>
                            </View>
                        </View>
                        <View style={styles.overallProgressBar}>
                            <View style={[styles.overallProgressFill, { width: `${getOverallProgress()}%` }]} />
                        </View>
                    </Card>

                    {/* Age Group Cards */}
                    {vaccineEntries.map((entry, index) => {
                        const completionPercentage = getCompletionPercentage(entry.originalAge, entry.vaccines);
                        const isEven = index % 2 === 0;

                        return (
                            <View key={entry.age} style={styles.ageGroupContainer}>
                                <Card style={[
                                    styles.ageGroupCard,
                                    isEven ? styles.alignRight : styles.alignLeft
                                ]}>
                                    {/* Age Header */}
                                    <View style={styles.ageHeader}>
                                        <View style={styles.ageTitleContainer}>
                                            <View style={[
                                                styles.ageDot,
                                                { backgroundColor: completionPercentage === 100 ? colors.success : colors.neonPurple }
                                            ]} />
                                            <Text style={styles.ageTitle}>{entry.age}</Text>
                                        </View>
                                        <View style={[
                                            styles.progressBadge,
                                            completionPercentage === 100 && styles.completedBadge
                                        ]}>
                                            <Text style={styles.progressBadgeText}>
                                                {completionPercentage === 100 ? '✓' : `${completionPercentage}%`}
                                            </Text>
                                        </View>
                                    </View>

                                    {/* Vaccine Count */}
                                    <Text style={styles.vaccineCount}>
                                        {entry.vaccines.length} vaccine{entry.vaccines.length > 1 ? 's' : ''}
                                    </Text>

                                    {/* Progress Bar */}
                                    <View style={styles.progressBar}>
                                        <View
                                            style={[
                                                styles.progressFill,
                                                { width: `${completionPercentage}%` },
                                                completionPercentage === 100 && styles.completedFill
                                            ]}
                                        />
                                    </View>

                                    {/* Vaccines List */}
                                    <View style={styles.vaccinesList}>
                                        {entry.vaccines.map((vaccine, vaccIndex) => {
                                            const isChecked = isVaccineChecked(entry.originalAge, vaccIndex);

                                            return (
                                                <TouchableOpacity
                                                    key={vaccIndex}
                                                    style={styles.vaccineItem}
                                                    onPress={() => handleVaccineCheck(entry.originalAge, vaccIndex, !isChecked)}
                                                    activeOpacity={0.7}
                                                >
                                                    <View style={[
                                                        styles.checkbox,
                                                        isChecked && styles.checkboxChecked
                                                    ]}>
                                                        {isChecked && (
                                                            <Ionicons name="checkmark" size={14} color={colors.white} />
                                                        )}
                                                    </View>
                                                    <Text style={[
                                                        styles.vaccineText,
                                                        isChecked && styles.vaccineTextChecked
                                                    ]}>
                                                        {vaccine}
                                                    </Text>
                                                </TouchableOpacity>
                                            );
                                        })}
                                    </View>
                                </Card>

                                {/* Connection Line */}
                                {index < vaccineEntries.length - 1 && (
                                    <View style={[
                                        styles.connectionContainer,
                                        isEven ? styles.connectionRight : styles.connectionLeft
                                    ]}>
                                        <LinearGradient
                                            colors={[colors.neonPurple, colors.mutedLavender]}
                                            style={styles.connectionLine}
                                        />
                                    </View>
                                )}
                            </View>
                        );
                    })}
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

    // Overall Progress Card
    overallCard: {
        padding: spacing.lg,
        marginBottom: spacing.xl,
    },
    overallHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    iconCircle: {
        width: 48,
        height: 48,
        borderRadius: 24,
        justifyContent: 'center',
        alignItems: 'center',
    },
    overallInfo: {
        flex: 1,
        marginLeft: spacing.md,
    },
    overallTitle: {
        ...typography.h3,
    },
    overallSubtitle: {
        ...typography.caption,
        marginTop: 2,
    },
    overallBadge: {
        backgroundColor: colors.neonPurple + '20',
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.md,
    },
    overallPercentage: {
        ...typography.h3,
        color: colors.neonPurple,
    },
    overallProgressBar: {
        height: 8,
        backgroundColor: colors.lightOrchid,
        borderRadius: 4,
        overflow: 'hidden',
    },
    overallProgressFill: {
        height: '100%',
        backgroundColor: colors.neonPurple,
        borderRadius: 4,
    },

    // Age Group Cards
    ageGroupContainer: {
        marginBottom: spacing.sm,
    },
    ageGroupCard: {
        padding: spacing.lg,
        width: '92%',
    },
    alignRight: {
        alignSelf: 'flex-end',
    },
    alignLeft: {
        alignSelf: 'flex-start',
    },
    ageHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.xs,
    },
    ageTitleContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
    },
    ageDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
    },
    ageTitle: {
        ...typography.h3,
    },
    progressBadge: {
        backgroundColor: colors.neonPurple,
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.sm,
        minWidth: 44,
        alignItems: 'center',
    },
    completedBadge: {
        backgroundColor: colors.success,
    },
    progressBadgeText: {
        ...typography.caption,
        color: colors.white,
        fontWeight: '600',
    },
    vaccineCount: {
        ...typography.caption,
        marginBottom: spacing.sm,
    },
    progressBar: {
        height: 4,
        backgroundColor: colors.lightOrchid,
        borderRadius: 2,
        marginBottom: spacing.md,
        overflow: 'hidden',
    },
    progressFill: {
        height: '100%',
        backgroundColor: colors.neonPurple,
        borderRadius: 2,
    },
    completedFill: {
        backgroundColor: colors.success,
    },
    vaccinesList: {
        gap: spacing.sm,
    },
    vaccineItem: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: spacing.sm,
        paddingHorizontal: spacing.sm,
        backgroundColor: colors.white,
        borderRadius: borderRadius.sm,
        borderWidth: 1,
        borderColor: colors.lightOrchid,
    },
    checkbox: {
        width: 22,
        height: 22,
        borderRadius: 6,
        borderWidth: 2,
        borderColor: colors.lightOrchid,
        backgroundColor: colors.white,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: spacing.sm,
    },
    checkboxChecked: {
        backgroundColor: colors.neonPurple,
        borderColor: colors.neonPurple,
    },
    vaccineText: {
        ...typography.bodySmall,
        flex: 1,
        color: colors.inkPurple,
    },
    vaccineTextChecked: {
        textDecorationLine: 'line-through',
        color: colors.dustyPurple,
    },

    // Connection Line
    connectionContainer: {
        height: 24,
        justifyContent: 'center',
        marginVertical: spacing.xs,
    },
    connectionRight: {
        alignItems: 'flex-end',
        paddingRight: '12%',
    },
    connectionLeft: {
        alignItems: 'flex-start',
        paddingLeft: '12%',
    },
    connectionLine: {
        width: 3,
        height: 20,
        borderRadius: 2,
    },
});
