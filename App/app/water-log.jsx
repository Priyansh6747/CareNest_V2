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
import { WaterAPI } from '../services/apiService';

const QUICK_AMOUNTS = [
    { label: '100ml', value: 100 },
    { label: '250ml', value: 250 },
    { label: '500ml', value: 500 },
    { label: '1L', value: 1000 },
];

export default function WaterLog() {
    const router = useRouter();
    const { user } = useUser();

    const [amount, setAmount] = useState('250');
    const [note, setNote] = useState('');
    const [loading, setLoading] = useState(false);

    const userId = user?.uid;

    const handleQuickAmount = (value) => {
        setAmount(value.toString());
    };

    const handleSubmit = async () => {
        if (!amount || parseFloat(amount) <= 0) {
            Alert.alert('Error', 'Please enter a valid amount');
            return;
        }

        setLoading(true);
        try {
            await WaterAPI.logWater(userId, {
                amount_ml: parseFloat(amount),
                note: note.trim() || null,
            });

            Alert.alert('Success', 'Water intake logged!', [
                { text: 'OK', onPress: () => router.back() },
            ]);
        } catch (err) {
            Alert.alert('Error', 'Failed to log water. Please try again.');
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
                        <Text style={styles.title}>Log Water</Text>
                        <View style={{ width: 40 }} />
                    </View>

                    {/* Water Icon */}
                    <View style={styles.iconContainer}>
                        <LinearGradient
                            colors={[colors.softBlue, colors.mutedLavender]}
                            style={styles.waterIcon}
                        >
                            <Ionicons name="water" size={48} color={colors.white} />
                        </LinearGradient>
                    </View>

                    {/* Quick Amounts */}
                    <Text style={styles.label}>Quick Add</Text>
                    <View style={styles.quickButtons}>
                        {QUICK_AMOUNTS.map((item) => (
                            <TouchableOpacity
                                key={item.value}
                                style={[
                                    styles.quickButton,
                                    amount === item.value.toString() && styles.quickButtonActive,
                                ]}
                                onPress={() => handleQuickAmount(item.value)}
                            >
                                <Text
                                    style={[
                                        styles.quickButtonText,
                                        amount === item.value.toString() && styles.quickButtonTextActive,
                                    ]}
                                >
                                    {item.label}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    {/* Custom Amount */}
                    <View style={styles.form}>
                        <Input
                            label="Custom Amount (ml)"
                            value={amount}
                            onChangeText={setAmount}
                            placeholder="Enter amount in ml"
                            keyboardType="numeric"
                        />

                        <Input
                            label="Note (Optional)"
                            value={note}
                            onChangeText={setNote}
                            placeholder="e.g., Morning glass, With meal"
                        />

                        <View style={styles.buttonContainer}>
                            <Button
                                title="Log Water"
                                onPress={handleSubmit}
                                loading={loading}
                                icon={<Ionicons name="water" size={20} color={colors.white} />}
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
        marginBottom: spacing.lg,
        marginTop: spacing.md,
    },
    backButton: {
        padding: spacing.sm,
    },
    title: {
        ...typography.h2,
    },
    iconContainer: {
        alignItems: 'center',
        marginBottom: spacing.xl,
    },
    waterIcon: {
        width: 100,
        height: 100,
        borderRadius: 50,
        justifyContent: 'center',
        alignItems: 'center',
        ...shadows.glow,
    },
    label: {
        ...typography.bodySmall,
        fontWeight: '600',
        color: colors.inkPurple,
        marginBottom: spacing.sm,
    },
    quickButtons: {
        flexDirection: 'row',
        gap: spacing.sm,
        marginBottom: spacing.xl,
    },
    quickButton: {
        flex: 1,
        paddingVertical: spacing.md,
        borderRadius: borderRadius.md,
        backgroundColor: 'rgba(254, 253, 254, 0.85)',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: colors.lightOrchid,
        ...shadows.light,
    },
    quickButtonActive: {
        backgroundColor: colors.softBlue,
        borderColor: colors.softBlue,
    },
    quickButtonText: {
        ...typography.body,
        fontWeight: '600',
        color: colors.mutedPurple,
    },
    quickButtonTextActive: {
        color: colors.white,
    },
    form: {
        gap: spacing.md,
    },
    buttonContainer: {
        marginTop: spacing.lg,
    },
});
