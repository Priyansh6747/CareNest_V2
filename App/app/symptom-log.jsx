import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    SafeAreaView,
    StatusBar,
    Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useUser } from '../hooks/auth_context';
import Input from '../components/Input';
import Button from '../components/Button';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';
import { SymptomsAPI, UserAPI } from '../services/apiService';

const SEVERITY_LEVELS = [1, 2, 3, 4, 5];

export default function SymptomLog() {
    const router = useRouter();
    const { user } = useUser();

    const [activeTab, setActiveTab] = useState('symptom'); // 'symptom' or 'allergy'
    
    // Symptom Form State
    const [symptomName, setSymptomName] = useState('');
    const [severity, setSeverity] = useState(3);
    const [description, setDescription] = useState('');
    
    // Allergy Form State
    const [allergies, setAllergies] = useState([]);
    const [newAllergy, setNewAllergy] = useState('');
    const [loadingAllergies, setLoadingAllergies] = useState(false);
    
    // Joint Loading State for submission
    const [loading, setLoading] = useState(false);

    const userId = user?.uid;

    React.useEffect(() => {
        if (activeTab === 'allergy' && userId) {
            loadAllergies();
        }
    }, [activeTab, userId]);

    const loadAllergies = async () => {
        setLoadingAllergies(true);
        try {
            const data = await UserAPI.getAllergies(userId);
            setAllergies(data.allergies || []);
        } catch (err) {
            console.log('Failed to load allergies', err);
        } finally {
            setLoadingAllergies(false);
        }
    };

    const handleAddAllergy = async () => {
        if (!newAllergy.trim()) {
            Alert.alert('Error', 'Please enter an allergy name');
            return;
        }

        setLoading(true);
        try {
            const response = await UserAPI.addAllergy(userId, newAllergy.trim());
            setAllergies(response.allergies);
            setNewAllergy('');
            Alert.alert('Success', 'Allergy added successfully');
        } catch (err) {
            Alert.alert('Error', 'Failed to add allergy');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteAllergy = async (allergyName) => {
        Alert.alert(
            "Remove Allergy",
            `Are you sure you want to remove "${allergyName}"?`,
            [
                { text: "Cancel", style: "cancel" },
                { 
                    text: "Remove", 
                    style: "destructive",
                    onPress: async () => {
                        try {
                            const response = await UserAPI.deleteAllergy(userId, allergyName);
                            setAllergies(response.allergies);
                        } catch (err) {
                            Alert.alert('Error', 'Failed to remove allergy');
                        }
                    }
                }
            ]
        );
    };

    const handleSubmit = async () => {
        if (!symptomName.trim()) {
            Alert.alert('Error', 'Please enter a symptom name');
            return;
        }

        setLoading(true);
        try {
            await SymptomsAPI.reportSymptom(userId, {
                symptom_name: symptomName.trim(),
                severity,
                description: description.trim() || null,
            });

            Alert.alert('Success', 'Symptom logged successfully!', [
                { text: 'OK', onPress: () => router.back() },
            ]);
        } catch (err) {
            Alert.alert('Error', 'Failed to log symptom. Please try again.');
        } finally {
            setLoading(false);
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
                        <Text style={styles.title}>Log Symptom</Text>
                        <View style={{ width: 40 }} />
                    </View>

                    {/* Tab Switcher */}
                    <View style={styles.tabContainer}>
                        <TouchableOpacity 
                            style={[styles.tab, activeTab === 'symptom' && styles.activeTab]}
                            onPress={() => setActiveTab('symptom')}
                        >
                            <Text style={[styles.tabText, activeTab === 'symptom' && styles.activeTabText]}>Log Symptom</Text>
                        </TouchableOpacity>
                        <TouchableOpacity 
                            style={[styles.tab, activeTab === 'allergy' && styles.activeTab]}
                            onPress={() => setActiveTab('allergy')}
                        >
                            <Text style={[styles.tabText, activeTab === 'allergy' && styles.activeTabText]}>Manage Allergies</Text>
                        </TouchableOpacity>
                    </View>

                    {activeTab === 'symptom' ? (
                        /* Symptom Form */
                        <View style={styles.form}>
                            <Input
                                label="Symptom Name"
                                value={symptomName}
                                onChangeText={setSymptomName}
                                placeholder="e.g., Headache, Nausea, Fatigue"
                            />

                            {/* Severity Selector */}
                            <View style={styles.severitySection}>
                                <Text style={styles.label}>Severity Level</Text>
                                <View style={styles.severityButtons}>
                                    {SEVERITY_LEVELS.map((level) => (
                                        <TouchableOpacity
                                            key={level}
                                            style={[
                                                styles.severityButton,
                                                severity === level && styles.severityButtonActive,
                                            ]}
                                            onPress={() => setSeverity(level)}
                                        >
                                            {severity === level ? (
                                                <LinearGradient
                                                    colors={[colors.neonPurple, colors.mutedLavender]}
                                                    style={styles.severityButtonGradient}
                                                >
                                                    <Text style={styles.severityTextActive}>{level}</Text>
                                                </LinearGradient>
                                            ) : (
                                                <Text style={styles.severityText}>{level}</Text>
                                            )}
                                        </TouchableOpacity>
                                    ))}
                                </View>
                                <View style={styles.severityLabels}>
                                    <Text style={styles.severityLabel}>Mild</Text>
                                    <Text style={styles.severityLabel}>Severe</Text>
                                </View>
                            </View>

                            <Input
                                label="Description (Optional)"
                                value={description}
                                onChangeText={setDescription}
                                placeholder="Describe how you're feeling..."
                                multiline
                                numberOfLines={4}
                            />

                            <View style={styles.buttonContainer}>
                                <Button
                                    title="Log Symptom"
                                    onPress={handleSubmit}
                                    loading={loading}
                                    icon={<Ionicons name="medical" size={20} color={colors.white} />}
                                />
                            </View>
                        </View>
                    ) : (
                        /* Allergy Form */
                        <View style={styles.form}>
                            <View style={styles.infoBox}>
                                <Ionicons name="information-circle-outline" size={20} color={colors.inkPurple} />
                                <Text style={styles.infoText}>
                                    Logging your allergies helps us personalize your meal recommendations.
                                </Text>
                            </View>

                            <View style={styles.allergyList}>
                                {allergies.map((allergy, index) => (
                                    <View key={index} style={styles.allergyItem}>
                                        <Text style={styles.allergyName}>{allergy}</Text>
                                        <TouchableOpacity 
                                            onPress={() => handleDeleteAllergy(allergy)}
                                            style={styles.deleteButton}
                                        >
                                            <Ionicons name="close-circle" size={20} color={colors.dustyPurple} />
                                        </TouchableOpacity>
                                    </View>
                                ))}
                                {allergies.length === 0 && !loadingAllergies && (
                                    <Text style={styles.emptyText}>No allergies recorded yet.</Text>
                                )}
                            </View>

                            <View style={styles.divider} />

                            <Text style={styles.sectionTitle}>Add New Allergy</Text>
                            <Input
                                label="Allergy Name"
                                value={newAllergy}
                                onChangeText={setNewAllergy}
                                placeholder="e.g., Peanuts, Dairy, Gluten"
                            />

                            <View style={styles.buttonContainer}>
                                <Button
                                    title="Add Allergy"
                                    onPress={handleAddAllergy}
                                    loading={loading}
                                    icon={<Ionicons name="add-circle-outline" size={20} color={colors.white} />}
                                />
                            </View>
                        </View>
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
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: spacing.xl,
        marginTop: spacing.md,
    },
    backButton: {
        padding: spacing.sm,
    },
    title: {
        ...typography.h2,
    },
    form: {
        gap: spacing.md,
    },
    label: {
        ...typography.bodySmall,
        fontWeight: '600',
        color: colors.inkPurple,
        marginBottom: spacing.sm,
    },
    severitySection: {
        marginBottom: spacing.md,
    },
    severityButtons: {
        flexDirection: 'row',
        gap: spacing.sm,
    },
    severityButton: {
        flex: 1,
        aspectRatio: 1,
        maxWidth: 56,
        borderRadius: borderRadius.md,
        backgroundColor: 'rgba(254, 253, 254, 0.85)',
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: colors.lightOrchid,
        ...shadows.light,
    },
    severityButtonActive: {
        borderWidth: 0,
    },
    severityButtonGradient: {
        width: '100%',
        height: '100%',
        borderRadius: borderRadius.md,
        justifyContent: 'center',
        alignItems: 'center',
    },
    severityText: {
        ...typography.h3,
        color: colors.mutedPurple,
    },
    severityTextActive: {
        ...typography.h3,
        color: colors.white,
    },
    severityLabels: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginTop: spacing.xs,
        paddingHorizontal: spacing.xs,
    },
    severityLabel: {
        ...typography.caption,
    },
    buttonContainer: {
        marginTop: spacing.lg,
    },
    // Tab Styles
    tabContainer: {
        flexDirection: 'row',
        backgroundColor: colors.white + '80',
        borderRadius: borderRadius.md,
        padding: 4,
        marginBottom: spacing.xl,
    },
    tab: {
        flex: 1,
        paddingVertical: spacing.sm,
        alignItems: 'center',
        borderRadius: borderRadius.sm,
    },
    activeTab: {
        backgroundColor: colors.white,
        ...shadows.light,
    },
    tabText: {
        ...typography.bodySmall,
        color: colors.dustyPurple,
        fontWeight: '600',
    },
    activeTabText: {
        color: colors.neonPurple,
    },
    // Allergy Styles
    infoBox: {
        flexDirection: 'row',
        gap: spacing.sm,
        backgroundColor: colors.paleCream,
        padding: spacing.md,
        borderRadius: borderRadius.md,
        marginBottom: spacing.md,
    },
    infoText: {
        ...typography.caption,
        color: colors.inkPurple,
        flex: 1,
    },
    allergyList: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
        marginBottom: spacing.lg,
    },
    allergyItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.white,
        paddingLeft: spacing.md,
        paddingRight: spacing.xs,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.full,
        borderWidth: 1,
        borderColor: colors.lightLavendar,
        gap: spacing.xs,
    },
    allergyName: {
        ...typography.bodySmall,
        color: colors.inkPurple,
    },
    deleteButton: {
        padding: 2,
    },
    emptyText: {
        ...typography.body,
        color: colors.dustyPurple,
        fontStyle: 'italic',
        width: '100%',
        textAlign: 'center',
        paddingVertical: spacing.md,
    },
    divider: {
        height: 1,
        backgroundColor: colors.lightLavendar,
        marginVertical: spacing.md,
    },
    sectionTitle: {
        ...typography.h3,
        marginBottom: spacing.md,
        color: colors.inkPurple,
    },
});
