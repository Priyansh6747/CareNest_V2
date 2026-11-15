import React from 'react';
import {
    View,
    Text,
    StyleSheet,
    TextInput,
    TouchableOpacity,
    Animated,
    Pressable,
    Platform,
    ScrollView,
} from 'react-native';
import { createUserWithEmailAndPassword, sendEmailVerification } from 'firebase/auth';
import { auth } from '../firebaseConfig';
import { showAlert } from '../utils/alert';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';

const BottomSheet = ({ setStatus }) => {
    const slide = React.useRef(new Animated.Value(320)).current;
    const [email, setEmail] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

    const handleRegister = async () => {
        if (email === '' || password === '') {
            showAlert('Error', 'Email and password are required');
            return;
        }

        setIsLoading(true);

        try {
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;

            await sendEmailVerification(user);
            showAlert('Account created', 'Check your inbox to verify your email.');
            closeModal();
        } catch (error) {
            let errorMessage = 'An error occurred during registration';

            switch (error.code) {
                case 'auth/email-already-in-use':
                    errorMessage = 'This email is already registered';
                    break;
                case 'auth/weak-password':
                    errorMessage = 'Password should be at least 6 characters';
                    break;
                case 'auth/invalid-email':
                    errorMessage = 'Please enter a valid email address';
                    break;
                default:
                    errorMessage = error.message;
            }

            showAlert('Registration Failed', errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        Animated.timing(slide, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
        }).start();
    }, []);

    const closeModal = () => {
        Animated.timing(slide, {
            toValue: 320,
            duration: 250,
            useNativeDriver: true,
        }).start(() => setStatus(false));
    };

    return (
        <Pressable onPress={closeModal} style={styles.backdrop}>
            {/* Stop propagation so taps inside the sheet do not dismiss it. */}
            <Pressable onPress={() => {}} style={styles.sheetWrap}>
                <Animated.View
                    style={[styles.sheet, { transform: [{ translateY: slide }] }]}
                >
                    <View style={styles.grabber} />
                    <ScrollView
                        contentContainerStyle={styles.scrollContent}
                        keyboardShouldPersistTaps="handled"
                        showsVerticalScrollIndicator={false}
                    >
                        <Text style={styles.title}>Create account</Text>
                        <Text style={styles.subtitle}>
                            Join CareNest to track your pregnancy journey
                        </Text>

                        <Text style={styles.label}>Email</Text>
                        <TextInput
                            placeholder="you@example.com"
                            placeholderTextColor={colors.dustyPurple}
                            style={styles.input}
                            onChangeText={setEmail}
                            keyboardType="email-address"
                            autoCapitalize="none"
                            autoCorrect={false}
                            autoComplete="email"
                            editable={!isLoading}
                        />

                        <Text style={styles.label}>Password</Text>
                        <TextInput
                            placeholder="At least 6 characters"
                            placeholderTextColor={colors.dustyPurple}
                            style={styles.input}
                            secureTextEntry
                            onChangeText={setPassword}
                            autoCapitalize="none"
                            autoCorrect={false}
                            editable={!isLoading}
                        />

                        <TouchableOpacity
                            onPress={handleRegister}
                            style={[styles.button, isLoading && styles.buttonDisabled]}
                            disabled={isLoading}
                            activeOpacity={0.85}
                        >
                            <Text style={styles.buttonText}>
                                {isLoading ? 'Creating Account…' : 'Register'}
                            </Text>
                        </TouchableOpacity>

                        <TouchableOpacity onPress={closeModal} style={styles.cancelWrap}>
                            <Text style={styles.cancelText}>Cancel</Text>
                        </TouchableOpacity>
                    </ScrollView>
                </Animated.View>
            </Pressable>
        </Pressable>
    );
};

export default BottomSheet;

const styles = StyleSheet.create({
    backdrop: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(31, 6, 51, 0.45)',
        justifyContent: 'flex-end',
        alignItems: 'center',
    },
    sheetWrap: {
        width: '100%',
        maxWidth: 520,
        justifyContent: 'flex-end',
    },
    sheet: {
        width: '100%',
        backgroundColor: colors.white,
        borderTopLeftRadius: borderRadius.xl,
        borderTopRightRadius: borderRadius.xl,
        paddingHorizontal: spacing.lg,
        paddingTop: spacing.sm,
        paddingBottom: Platform.OS === 'web' ? spacing.lg : spacing.xl,
        ...shadows.medium,
    },
    grabber: {
        alignSelf: 'center',
        width: 44,
        height: 5,
        borderRadius: 3,
        backgroundColor: colors.lightOrchid,
        marginBottom: spacing.md,
    },
    scrollContent: {
        flexGrow: 1,
    },
    title: {
        ...typography.h2,
        textAlign: 'center',
        marginBottom: spacing.xs,
    },
    subtitle: {
        ...typography.bodySmall,
        color: colors.mutedPurple,
        textAlign: 'center',
        marginBottom: spacing.lg,
    },
    label: {
        ...typography.bodySmall,
        fontWeight: '600',
        color: colors.inkPurple,
        marginBottom: spacing.xs,
    },
    input: {
        width: '100%',
        borderRadius: borderRadius.md,
        borderWidth: 1,
        borderColor: colors.lightOrchid,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.md,
        marginBottom: spacing.md,
        fontSize: 16,
        color: colors.inkPurple,
        backgroundColor: colors.white,
    },
    button: {
        paddingVertical: spacing.md,
        borderRadius: borderRadius.md,
        backgroundColor: colors.neonPurple,
        alignItems: 'center',
        marginTop: spacing.sm,
        ...shadows.glow,
    },
    buttonText: {
        fontSize: 17,
        fontWeight: '700',
        color: colors.white,
    },
    buttonDisabled: {
        opacity: 0.6,
    },
    cancelWrap: {
        alignItems: 'center',
        paddingVertical: spacing.md,
    },
    cancelText: {
        ...typography.body,
        color: colors.mutedPurple,
        fontWeight: '600',
    },
});
