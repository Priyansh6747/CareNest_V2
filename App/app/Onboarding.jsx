import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    SafeAreaView,
    StatusBar,
    Alert,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { updateProfile } from 'firebase/auth';
import { auth } from '../firebaseConfig';

import { useUser } from '../hooks/auth_context';
import Input from '../components/Input';
import Button from '../components/Button';
import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius, glassmorphism } from '../theme';
import { UserAPI } from '../services/apiService';

const STEPS = ['profile', 'maternal', 'consent'];

export default function Onboarding() {
    const { user, refreshUser } = useUser();

    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);

    // Profile data
    const [displayName, setDisplayName] = useState('');
    const [phone, setPhone] = useState('');

    // Maternal data
    const [dueDate, setDueDate] = useState('');
    const [trimester, setTrimester] = useState('1');
    const [age, setAge] = useState('');
    const [heightCm, setHeightCm] = useState('');
    const [weightKg, setWeightKg] = useState('');

    const handleNext = async () => {
        if (currentStep === 0) {
            // Validate profile
            if (!displayName.trim()) {
                Alert.alert('Required', 'Please enter your name');
                return;
            }
            setCurrentStep(1);
        } else if (currentStep === 1) {
            // Validate maternal info
            if (!age || !heightCm || !weightKg) {
                Alert.alert('Required', 'Please fill in all fields');
                return;
            }
            setCurrentStep(2);
        } else if (currentStep === 2) {
            // Complete onboarding
            await completeOnboarding();
        }
    };

    const completeOnboarding = async () => {
        setLoading(true);
        try {
            // 1. Update Firebase display name
            await updateProfile(auth.currentUser, {
                displayName: displayName.trim(),
            });

            // 2. Call backend API to initialize onboarding
            await UserAPI.initOnboarding({
                user: {
                    firebase_uid: user.uid,
                    email: user.email,
                    display_name: displayName.trim(),
                    phone: phone || null,
                },
                maternal: {
                    due_date: dueDate || null,
                    trimester: parseInt(trimester, 10),
                    age: parseInt(age, 10),
                    height_cm: parseFloat(heightCm),
                    weight_kg: parseFloat(weightKg),
                },
                consent: {
                    data_collection: true,
                    health_tracking: true,
                    notifications: true,
                },
            });

            // 3. Refresh user to trigger navigation
            await refreshUser();

        } catch (error) {
            console.log('Onboarding error:', error);
            Alert.alert('Error', 'Failed to complete onboarding. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const renderStepIndicator = () => (
        <View style={styles.stepIndicator}>
            {STEPS.map((step, index) => (
                <View
                    key={step}
                    style={[
                        styles.stepDot,
                        index <= currentStep && styles.stepDotActive,
                    ]}
                />
            ))}
        </View>
    );

    const renderProfileStep = () => (
        <View style={styles.stepContent}>
            <View style={styles.iconContainer}>
                <LinearGradient
                    colors={[colors.neonPurple, colors.mutedLavender]}
                    style={styles.iconCircle}
                >
                    <Ionicons name="person" size={40} color={colors.white} />
                </LinearGradient>
            </View>

            <Text style={styles.stepTitle}>Let's get to know you</Text>
            <Text style={styles.stepSubtitle}>Tell us a bit about yourself</Text>

            <View style={styles.form}>
                <Input
                    label="Your Name"
                    value={displayName}
                    onChangeText={setDisplayName}
                    placeholder="Enter your name"
                />
                <Input
                    label="Phone (Optional)"
                    value={phone}
                    onChangeText={setPhone}
                    placeholder="Enter phone number"
                    keyboardType="phone-pad"
                />
            </View>
        </View>
    );

    const renderMaternalStep = () => (
        <View style={styles.stepContent}>
            <View style={styles.iconContainer}>
                <LinearGradient
                    colors={[colors.neonPurple, colors.mutedLavender]}
                    style={styles.iconCircle}
                >
                    <Ionicons name="heart" size={40} color={colors.white} />
                </LinearGradient>
            </View>

            <Text style={styles.stepTitle}>Pregnancy Details</Text>
            <Text style={styles.stepSubtitle}>Help us personalize your experience</Text>

            <View style={styles.form}>
                <Input
                    label="Your Age"
                    value={age}
                    onChangeText={setAge}
                    placeholder="e.g., 28"
                    keyboardType="numeric"
                />
                <View style={styles.row}>
                    <View style={styles.halfInput}>
                        <Input
                            label="Height (cm)"
                            value={heightCm}
                            onChangeText={setHeightCm}
                            placeholder="e.g., 165"
                            keyboardType="numeric"
                        />
                    </View>
                    <View style={styles.halfInput}>
                        <Input
                            label="Weight (kg)"
                            value={weightKg}
                            onChangeText={setWeightKg}
                            placeholder="e.g., 60"
                            keyboardType="numeric"
                        />
                    </View>
                </View>
                <Input
                    label="Due Date (Optional)"
                    value={dueDate}
                    onChangeText={setDueDate}
                    placeholder="YYYY-MM-DD"
                />
            </View>
        </View>
    );

    const renderConsentStep = () => (
        <View style={styles.stepContent}>
            <View style={styles.iconContainer}>
                <LinearGradient
                    colors={[colors.neonPurple, colors.mutedLavender]}
                    style={styles.iconCircle}
                >
                    <Ionicons name="shield-checkmark" size={40} color={colors.white} />
                </LinearGradient>
            </View>

            <Text style={styles.stepTitle}>Almost Done!</Text>
            <Text style={styles.stepSubtitle}>Review and confirm</Text>

            <Card style={styles.summaryCard}>
                <View style={styles.summaryRow}>
                    <Ionicons name="person" size={20} color={colors.neonPurple} />
                    <Text style={styles.summaryText}>{displayName}</Text>
                </View>
                <View style={styles.summaryRow}>
                    <Ionicons name="calendar" size={20} color={colors.neonPurple} />
                    <Text style={styles.summaryText}>Age: {age} years</Text>
                </View>
                <View style={styles.summaryRow}>
                    <Ionicons name="fitness" size={20} color={colors.neonPurple} />
                    <Text style={styles.summaryText}>{heightCm}cm, {weightKg}kg</Text>
                </View>
            </Card>

            <Card style={styles.consentCard}>
                <Text style={styles.consentTitle}>By continuing, you agree to:</Text>
                <View style={styles.consentItem}>
                    <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                    <Text style={styles.consentText}>Data collection for health tracking</Text>
                </View>
                <View style={styles.consentItem}>
                    <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                    <Text style={styles.consentText}>Personalized health recommendations</Text>
                </View>
                <View style={styles.consentItem}>
                    <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                    <Text style={styles.consentText}>Health-related notifications</Text>
                </View>
            </Card>
        </View>
    );

    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <SafeAreaView style={styles.safeArea}>
                <KeyboardAvoidingView
                    style={styles.keyboardView}
                    behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                >
                    {renderStepIndicator()}

                    <ScrollView
                        style={styles.scrollView}
                        contentContainerStyle={styles.scrollContent}
                        showsVerticalScrollIndicator={false}
                    >
                        {currentStep === 0 && renderProfileStep()}
                        {currentStep === 1 && renderMaternalStep()}
                        {currentStep === 2 && renderConsentStep()}
                    </ScrollView>

                    <View style={styles.buttonContainer}>
                        {currentStep > 0 && (
                            <Button
                                title="Back"
                                onPress={() => setCurrentStep(currentStep - 1)}
                                variant="outlined"
                                style={{ flex: 1, marginRight: spacing.sm }}
                            />
                        )}
                        <Button
                            title={currentStep === 2 ? "Complete Setup" : "Continue"}
                            onPress={handleNext}
                            loading={loading}
                            style={{ flex: currentStep > 0 ? 1 : undefined, width: currentStep === 0 ? '100%' : undefined }}
                            icon={currentStep === 2 ? <Ionicons name="checkmark" size={20} color={colors.white} /> : undefined}
                        />
                    </View>
                </KeyboardAvoidingView>
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
    keyboardView: {
        flex: 1,
    },
    stepIndicator: {
        flexDirection: 'row',
        justifyContent: 'center',
        gap: spacing.sm,
        paddingVertical: spacing.lg,
    },
    stepDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
        backgroundColor: colors.lightOrchid,
    },
    stepDotActive: {
        backgroundColor: colors.neonPurple,
        width: 24,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: spacing.lg,
        paddingTop: 0,
    },
    stepContent: {
        alignItems: 'center',
    },
    iconContainer: {
        marginBottom: spacing.lg,
    },
    iconCircle: {
        width: 80,
        height: 80,
        borderRadius: 40,
        justifyContent: 'center',
        alignItems: 'center',
    },
    stepTitle: {
        ...typography.h1,
        textAlign: 'center',
        marginBottom: spacing.xs,
    },
    stepSubtitle: {
        ...typography.body,
        color: colors.mutedPurple,
        textAlign: 'center',
        marginBottom: spacing.xl,
    },
    form: {
        width: '100%',
    },
    row: {
        flexDirection: 'row',
        gap: spacing.md,
    },
    halfInput: {
        flex: 1,
    },
    summaryCard: {
        width: '100%',
        padding: spacing.lg,
        marginBottom: spacing.md,
    },
    summaryRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.md,
        marginBottom: spacing.sm,
    },
    summaryText: {
        ...typography.body,
        flex: 1,
    },
    consentCard: {
        width: '100%',
        padding: spacing.lg,
    },
    consentTitle: {
        ...typography.bodySmall,
        fontWeight: '600',
        marginBottom: spacing.md,
    },
    consentItem: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        marginBottom: spacing.sm,
    },
    consentText: {
        ...typography.bodySmall,
        flex: 1,
    },
    buttonContainer: {
        flexDirection: 'row',
        padding: spacing.lg,
        paddingBottom: spacing.xl,
    },
});