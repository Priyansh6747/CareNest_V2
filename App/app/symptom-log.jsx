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
import { SymptomsAPI } from '../services/apiService';

const SEVERITY_LEVELS = [1, 2, 3, 4, 5];

export default function SymptomLog() {
    const router = useRouter();
    const { user } = useUser();

    const [symptomName, setSymptomName] = useState('');
    const [severity, setSeverity] = useState(3);
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);

    const userId = user?.uid;

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

                    {/* Form */}
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
});
