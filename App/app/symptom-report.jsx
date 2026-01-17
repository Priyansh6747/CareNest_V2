import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    SafeAreaView,
    StatusBar,
    Modal,
    TextInput,
    Alert,
    Pressable,
    ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useUser } from '../hooks/auth_context';
import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';
import { SymptomsAPI, MemoryAPI } from '../services/apiService';

const SEVERITY_LEVELS = [1, 2, 3, 4, 5];

export default function SymptomReport() {
    const router = useRouter();
    const { user } = useUser();

    const [frequencies, setFrequencies] = useState([]);
    const [recentLogs, setRecentLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generatingSummary, setGeneratingSummary] = useState(false);
    
    // Edit Modal State
    const [modalVisible, setModalVisible] = useState(false);
    const [editingSymptom, setEditingSymptom] = useState(null);
    const [editSeverity, setEditSeverity] = useState(3);
    const [editNotes, setEditNotes] = useState('');
    const [saving, setSaving] = useState(false);

    const userId = user?.uid;

    useEffect(() => {
        if (userId) {
            loadData();
        }
    }, [userId]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [freqData, logsData] = await Promise.all([
                SymptomsAPI.getAllFrequencies(userId, 30),
                SymptomsAPI.getRecentSymptoms(userId, { days: 30, limit: 20 })
            ]);
            setFrequencies(freqData || []);
            setRecentLogs(logsData || []);
        } catch (err) {
            console.log('Failed to load symptom data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleEditSymptom = (symptom) => {
        setEditingSymptom(symptom);
        setEditSeverity(symptom.severity);
        setEditNotes(symptom.description || '');
        setModalVisible(true);
    };

    const handleDeleteSymptom = (symptomId) => {
        Alert.alert(
            "Delete Log",
            "Are you sure you want to delete this symptom log?",
            [
                { text: "Cancel", style: "cancel" },
                { 
                    text: "Delete", 
                    style: "destructive",
                    onPress: async () => {
                        try {
                            await SymptomsAPI.deleteSymptom(userId, symptomId);
                            // Optimistic update
                            setRecentLogs(prev => prev.filter(log => log.id !== symptomId));
                            // Reload analysis to keep charts satisfying
                            const newFreq = await SymptomsAPI.getAllFrequencies(userId, 30);
                            setFrequencies(newFreq || []);
                        } catch (err) {
                            Alert.alert('Error', 'Failed to delete symptom');
                        }
                    }
                }
            ]
        );
    };

    const handleSaveEdit = async () => {
        if (!editingSymptom) return;
        setSaving(true);
        try {
            await SymptomsAPI.updateSymptom(userId, editingSymptom.id, {
                severity: editSeverity,
                description: editNotes
            });
            
            setModalVisible(false);
            setEditingSymptom(null);
            
            // Reload data
            loadData();
            Alert.alert('Success', 'Symptom updated successfully');
        } catch (err) {
            Alert.alert('Error', 'Failed to update symptom');
        } finally {
            setSaving(false);
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

                    {/* Recent Logs Section */}
                    {recentLogs.length > 0 && (
                        <View style={styles.sectionContainer}>
                            <Text style={styles.sectionTitle}>Recent Logs</Text>
                            {recentLogs.map((log, index) => (
                                <Card key={index} style={styles.logCard}>
                                    <View style={styles.logHeader}>
                                        <View style={styles.logTitleRow}>
                                            <View style={[styles.dot, { backgroundColor: getSeverityColor(log.severity) }]} />
                                            <Text style={styles.logTitle}>{log.symptom_name}</Text>
                                        </View>
                                        <Text style={styles.logDate}>
                                            {new Date(log.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                        </Text>
                                    </View>
                                    
                                    {log.description && (
                                        <Text style={styles.logDescription} numberOfLines={2}>
                                            {log.description}
                                        </Text>
                                    )}

                                    <View style={styles.logActions}>
                                        <TouchableOpacity 
                                            style={styles.actionButton}
                                            onPress={() => handleEditSymptom(log)}
                                        >
                                            <Ionicons name="create-outline" size={18} color={colors.neonPurple} />
                                            <Text style={styles.actionText}>Edit</Text>
                                        </TouchableOpacity>
                                        <TouchableOpacity 
                                            style={styles.actionButton}
                                            onPress={() => handleDeleteSymptom(log.id)}
                                        >
                                            <Ionicons name="trash-outline" size={18} color={colors.coralPink} />
                                            <Text style={[styles.actionText, { color: colors.coralPink }]}>Delete</Text>
                                        </TouchableOpacity>
                                    </View>
                                </Card>
                            ))}
                        </View>
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

                {/* Edit Modal */}
                <Modal
                    animationType="fade"
                    transparent={true}
                    visible={modalVisible}
                    onRequestClose={() => setModalVisible(false)}
                >
                    <View style={styles.modalOverlay}>
                        <View style={styles.modalContent}>
                            <Text style={styles.modalTitle}>Edit Symptom</Text>
                            
                            <Text style={styles.modalLabel}>Severity</Text>
                            <View style={styles.severityRow}>
                                {SEVERITY_LEVELS.map((level) => (
                                    <TouchableOpacity
                                        key={level}
                                        style={[
                                            styles.modalSeverityBtn,
                                            editSeverity === level && styles.modalSeverityBtnActive
                                        ]}
                                        onPress={() => setEditSeverity(level)}
                                    >
                                        <Text style={[
                                            styles.modalSeverityText,
                                            editSeverity === level && styles.modalSeverityTextActive
                                        ]}>{level}</Text>
                                    </TouchableOpacity>
                                ))}
                            </View>

                            <Text style={styles.modalLabel}>Notes</Text>
                            <TextInput
                                style={styles.modalInput}
                                value={editNotes}
                                onChangeText={setEditNotes}
                                multiline
                                numberOfLines={3}
                                placeholder="Add notes..."
                            />

                            <View style={styles.modalButtons}>
                                <TouchableOpacity 
                                    style={[styles.modalButton, styles.cancelButton]}
                                    onPress={() => setModalVisible(false)}
                                >
                                    <Text style={styles.cancelButtonText}>Cancel</Text>
                                </TouchableOpacity>
                                <TouchableOpacity 
                                    style={[styles.modalButton, styles.saveButton]}
                                    onPress={handleSaveEdit}
                                    disabled={saving}
                                >
                                    {saving ? (
                                        <ActivityIndicator color="white" size="small" />
                                    ) : (
                                        <Text style={styles.saveButtonText}>Save</Text>
                                    )}
                                </TouchableOpacity>
                            </View>
                        </View>
                    </View>
                </Modal>
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
    // New Styles
    sectionContainer: {
        marginTop: spacing.lg,
        marginBottom: spacing.md,
    },
    sectionTitle: {
        ...typography.h3,
        marginBottom: spacing.sm,
        color: colors.inkPurple,
    },
    logCard: {
        marginBottom: spacing.sm,
        padding: spacing.md,
    },
    logHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.xs,
    },
    logTitleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
    },
    logTitle: {
        ...typography.body,
        fontWeight: '600',
        color: colors.midnight,
        textTransform: 'capitalize',
    },
    logDate: {
        ...typography.caption,
        color: colors.dustyPurple,
    },
    logDescription: {
        ...typography.caption,
        color: colors.slate,
        marginBottom: spacing.sm,
        marginTop: spacing.xs,
    },
    logActions: {
        flexDirection: 'row',
        justifyContent: 'flex-end',
        gap: spacing.lg,
        marginTop: spacing.xs,
        borderTopWidth: 1,
        borderTopColor: colors.lightLavendar,
        paddingTop: spacing.sm,
    },
    actionButton: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
    },
    actionText: {
        fontSize: 12,
        fontWeight: '600',
        color: colors.neonPurple,
    },
    // Modal Styles
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: spacing.lg,
    },
    modalContent: {
        backgroundColor: colors.white,
        borderRadius: borderRadius.lg,
        padding: spacing.xl,
        width: '100%',
        maxWidth: 400,
        ...shadows.medium,
    },
    modalTitle: {
        ...typography.h2,
        marginBottom: spacing.lg,
        textAlign: 'center',
    },
    modalLabel: {
        ...typography.bodySmall,
        fontWeight: '600',
        color: colors.slate,
        marginBottom: spacing.sm,
    },
    severityRow: {
        flexDirection: 'row',
        gap: spacing.sm,
        marginBottom: spacing.lg,
    },
    modalSeverityBtn: {
        flex: 1,
        height: 40,
        borderRadius: borderRadius.md,
        borderWidth: 1,
        borderColor: colors.lightOrchid,
        justifyContent: 'center',
        alignItems: 'center',
    },
    modalSeverityBtnActive: {
        backgroundColor: colors.neonPurple,
        borderColor: colors.neonPurple,
    },
    modalSeverityText: {
        color: colors.dustyPurple,
        fontWeight: '600',
    },
    modalSeverityTextActive: {
        color: colors.white,
    },
    modalInput: {
        borderWidth: 1,
        borderColor: colors.lightLavendar,
        borderRadius: borderRadius.md,
        padding: spacing.md,
        height: 100,
        textAlignVertical: 'top',
        marginBottom: spacing.xl,
        backgroundColor: colors.paleCream,
    },
    modalButtons: {
        flexDirection: 'row',
        gap: spacing.md,
    },
    modalButton: {
        flex: 1,
        padding: spacing.md,
        borderRadius: borderRadius.md,
        alignItems: 'center',
    },
    cancelButton: {
        backgroundColor: colors.lightLavendar,
    },
    saveButton: {
        backgroundColor: colors.neonPurple,
    },
    cancelButtonText: {
        color: colors.inkPurple,
        fontWeight: '600',
    },
    saveButtonText: {
        color: colors.white,
        fontWeight: '600',
    },
});
