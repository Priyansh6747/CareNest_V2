import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    SafeAreaView,
    StatusBar,
    Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { sendEmailVerification } from 'firebase/auth';
import { auth } from '../firebaseConfig';

import { useUser } from '../hooks/auth_context';
import Button from '../components/Button';
import { colors, gradients, typography, spacing, borderRadius, glassmorphism } from '../theme';

export default function VerifyEmail() {
    const { user, refreshUser, logout } = useUser();
    const [resending, setResending] = useState(false);
    const [checking, setChecking] = useState(false);
    const [countdown, setCountdown] = useState(0);

    const email = user?.email || '';

    // Countdown timer for resend button
    useEffect(() => {
        if (countdown > 0) {
            const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [countdown]);

    const handleResendEmail = async () => {
        if (countdown > 0) return;

        setResending(true);
        try {
            await sendEmailVerification(auth.currentUser);
            Alert.alert('Email Sent', 'A new verification email has been sent.');
            setCountdown(60); // 60 second cooldown
        } catch (error) {
            let message = 'Failed to send email. Please try again.';
            if (error.code === 'auth/too-many-requests') {
                message = 'Too many requests. Please wait a few minutes.';
            }
            Alert.alert('Error', message);
        } finally {
            setResending(false);
        }
    };

    const handleCheckVerification = async () => {
        setChecking(true);
        try {
            await refreshUser();
            // The auth_context will automatically redirect if verified
            if (!auth.currentUser?.emailVerified) {
                Alert.alert('Not Verified', 'Your email is not verified yet. Please check your inbox and click the verification link.');
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to check verification status.');
        } finally {
            setChecking(false);
        }
    };

    const handleLogout = () => {
        Alert.alert(
            'Logout',
            'Are you sure you want to logout?',
            [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Logout', style: 'destructive', onPress: logout },
            ]
        );
    };

    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <SafeAreaView style={styles.safeArea}>
                <View style={styles.content}>
                    {/* Icon */}
                    <View style={styles.iconContainer}>
                        <LinearGradient
                            colors={[colors.neonPurple, colors.mutedLavender]}
                            style={styles.iconCircle}
                        >
                            <Ionicons name="mail-outline" size={48} color={colors.white} />
                        </LinearGradient>
                    </View>

                    {/* Title */}
                    <Text style={styles.title}>Verify Your Email</Text>
                    <Text style={styles.subtitle}>
                        We've sent a verification link to:
                    </Text>
                    <Text style={styles.email}>{email}</Text>

                    {/* Instructions */}
                    <View style={styles.instructions}>
                        <View style={styles.instructionRow}>
                            <View style={styles.stepNumber}>
                                <Text style={styles.stepText}>1</Text>
                            </View>
                            <Text style={styles.instructionText}>Check your email inbox</Text>
                        </View>
                        <View style={styles.instructionRow}>
                            <View style={styles.stepNumber}>
                                <Text style={styles.stepText}>2</Text>
                            </View>
                            <Text style={styles.instructionText}>Click the verification link</Text>
                        </View>
                        <View style={styles.instructionRow}>
                            <View style={styles.stepNumber}>
                                <Text style={styles.stepText}>3</Text>
                            </View>
                            <Text style={styles.instructionText}>Come back and tap "I've Verified"</Text>
                        </View>
                    </View>

                    {/* Buttons */}
                    <View style={styles.buttons}>
                        <Button
                            title={checking ? 'Checking...' : "I've Verified My Email"}
                            onPress={handleCheckVerification}
                            loading={checking}
                            icon={<Ionicons name="checkmark-circle" size={20} color={colors.white} />}
                        />

                        <Button
                            title={countdown > 0 ? `Resend in ${countdown}s` : 'Resend Email'}
                            onPress={handleResendEmail}
                            variant="outlined"
                            loading={resending}
                            disabled={countdown > 0}
                            icon={<Ionicons name="refresh" size={18} color={countdown > 0 ? colors.dustyPurple : colors.neonPurple} />}
                            style={{ marginTop: spacing.md }}
                        />

                        <Button
                            title="Use Different Account"
                            onPress={handleLogout}
                            variant="secondary"
                            icon={<Ionicons name="log-out-outline" size={18} color={colors.inkPurple} />}
                            style={{ marginTop: spacing.md }}
                        />
                    </View>
                </View>
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
    content: {
        flex: 1,
        padding: spacing.xl,
        justifyContent: 'center',
        alignItems: 'center',
    },
    iconContainer: {
        marginBottom: spacing.xl,
    },
    iconCircle: {
        width: 100,
        height: 100,
        borderRadius: 50,
        justifyContent: 'center',
        alignItems: 'center',
    },
    title: {
        ...typography.h1,
        textAlign: 'center',
        marginBottom: spacing.sm,
    },
    subtitle: {
        ...typography.body,
        color: colors.mutedPurple,
        textAlign: 'center',
    },
    email: {
        ...typography.body,
        fontWeight: '600',
        color: colors.neonPurple,
        textAlign: 'center',
        marginBottom: spacing.xl,
    },
    instructions: {
        ...glassmorphism.card,
        padding: spacing.lg,
        width: '100%',
        marginBottom: spacing.xl,
    },
    instructionRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.md,
        marginBottom: spacing.md,
    },
    stepNumber: {
        width: 28,
        height: 28,
        borderRadius: 14,
        backgroundColor: colors.neonPurple,
        justifyContent: 'center',
        alignItems: 'center',
    },
    stepText: {
        ...typography.bodySmall,
        fontWeight: '700',
        color: colors.white,
    },
    instructionText: {
        ...typography.body,
        flex: 1,
    },
    buttons: {
        width: '100%',
    },
});
