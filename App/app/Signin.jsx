import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    TextInput,
    ScrollView,
    StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { signInWithEmailAndPassword } from 'firebase/auth';

import { auth } from '../firebaseConfig';
import { showAlert } from '../utils/alert';
import useResponsive from '../hooks/useResponsive';
import BottomSheet from '../components/BottomSheet';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';

export default function Signin() {
    const [status, setStatus] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const insets = useSafeAreaInsets();
    const { pagePadding, cardMaxWidth } = useResponsive();

    const handleLogin = async () => {
        if (email === '' || password === '') {
            showAlert('Error', 'Password and email are required');
            return;
        }

        setLoading(true);

        try {
            const userCredentials = await signInWithEmailAndPassword(auth, email, password);
            const user = userCredentials.user;

            console.log('User logged in:', {
                uid: user.uid,
                email: user.email,
                emailVerified: user.emailVerified,
                displayName: user.displayName
            });
        } catch (error) {
            console.log('Authentication failed!');
            console.log('Failed email:', email);
            console.log('Firebase error code:', error.code);
            console.log('Error message:', error.message);

            let userMessage = 'Login failed. Please try again.';

            switch (error.code) {
                case 'auth/user-not-found':
                    userMessage = 'No account found with this email.';
                    break;
                case 'auth/wrong-password':
                    userMessage = 'Incorrect password.';
                    break;
                case 'auth/invalid-email':
                    userMessage = 'Invalid email format.';
                    break;
                case 'auth/user-disabled':
                    userMessage = 'This account has been disabled.';
                    break;
                case 'auth/too-many-requests':
                    userMessage = 'Too many failed attempts. Please try again later.';
                    break;
                case 'auth/invalid-credential':
                    userMessage = 'Invalid email or password.';
                    break;
            }

            showAlert('Login Failed', userMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <ScrollView
                contentContainerStyle={[
                    styles.scrollContent,
                    {
                        paddingTop: insets.top + spacing.xl,
                        paddingBottom: insets.bottom + spacing.xl,
                        paddingHorizontal: pagePadding,
                    },
                ]}
                keyboardShouldPersistTaps="handled"
                showsVerticalScrollIndicator={false}
            >
                <View style={[styles.card, cardMaxWidth ? { maxWidth: cardMaxWidth } : null]}>
                    <View style={styles.logoWrap}>
                        <LinearGradient
                            colors={[colors.neonPurple, colors.mutedLavender]}
                            style={styles.logo}
                        >
                            <Ionicons name="heart" size={34} color={colors.white} />
                        </LinearGradient>
                        <Text style={styles.brand}>CareNest</Text>
                        <Text style={styles.tagline}>Your pregnancy companion</Text>
                    </View>

                    <Text style={styles.title}>Welcome back</Text>

                    <View style={styles.inputContainer}>
                        <Text style={styles.label}>Email</Text>
                        <TextInput
                            placeholder="you@example.com"
                            placeholderTextColor={colors.dustyPurple}
                            style={styles.input}
                            onChangeText={setEmail}
                            value={email}
                            keyboardType="email-address"
                            autoCapitalize="none"
                            autoComplete="email"
                            editable={!loading}
                        />

                        <Text style={styles.label}>Password</Text>
                        <TextInput
                            placeholder="Your password"
                            placeholderTextColor={colors.dustyPurple}
                            style={styles.input}
                            secureTextEntry
                            onChangeText={setPassword}
                            value={password}
                            editable={!loading}
                            onSubmitEditing={handleLogin}
                        />
                    </View>

                    <TouchableOpacity
                        onPress={handleLogin}
                        style={[styles.buttonWrap, loading && styles.buttonDisabled]}
                        disabled={loading}
                        activeOpacity={0.85}
                    >
                        <LinearGradient
                            colors={[colors.neonPurple, colors.mutedLavender]}
                            start={{ x: 0, y: 0 }}
                            end={{ x: 1, y: 0 }}
                            style={styles.button}
                        >
                            <Text style={styles.buttonText}>
                                {loading ? 'Signing In…' : 'Login'}
                            </Text>
                        </LinearGradient>
                    </TouchableOpacity>

                    <TouchableOpacity
                        onPress={() => setStatus(true)}
                        disabled={loading}
                        style={styles.createAccountWrap}
                    >
                        <Text style={styles.createAccountText}>Create Account</Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>

            {status && <BottomSheet setStatus={setStatus} />}
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    scrollContent: {
        flexGrow: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    card: {
        width: '100%',
    },
    logoWrap: {
        alignItems: 'center',
        marginBottom: spacing.xl,
    },
    logo: {
        width: 72,
        height: 72,
        borderRadius: 36,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: spacing.md,
        ...shadows.glow,
    },
    brand: {
        ...typography.h1,
        color: colors.inkPurple,
    },
    tagline: {
        ...typography.bodySmall,
        color: colors.mutedPurple,
        marginTop: spacing.xs,
    },
    title: {
        ...typography.h2,
        marginBottom: spacing.lg,
    },
    inputContainer: {
        width: '100%',
    },
    label: {
        ...typography.bodySmall,
        fontWeight: '600',
        color: colors.inkPurple,
        marginBottom: spacing.xs,
    },
    input: {
        borderWidth: 1,
        borderColor: colors.lightOrchid,
        padding: spacing.md,
        marginBottom: spacing.md,
        borderRadius: borderRadius.md,
        backgroundColor: 'rgba(254, 253, 254, 0.9)',
        fontSize: 16,
        color: colors.inkPurple,
    },
    buttonWrap: {
        marginTop: spacing.md,
    },
    button: {
        paddingVertical: spacing.md,
        borderRadius: borderRadius.md,
        alignItems: 'center',
        ...shadows.glow,
    },
    buttonDisabled: {
        opacity: 0.6,
    },
    buttonText: {
        fontSize: 17,
        fontWeight: '700',
        color: colors.white,
    },
    createAccountWrap: {
        marginTop: spacing.lg,
        alignItems: 'center',
        paddingVertical: spacing.sm,
    },
    createAccountText: {
        color: colors.neonPurple,
        fontSize: 16,
        fontWeight: '600',
    },
});
