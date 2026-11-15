import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useUser } from '../hooks/auth_context';
import useResponsive from '../hooks/useResponsive';
import ScreenHeader from '../components/ScreenHeader';
import Input from '../components/Input';
import Button from '../components/Button';
import { showAlert } from '../utils/alert';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';
import { NutritionAPI } from '../services/apiService';

export default function MealLog() {
    const router = useRouter();
    const { user } = useUser();
    const insets = useSafeAreaInsets();
    const { isWeb, pagePadding, cardMaxWidth } = useResponsive();

    const [mealName, setMealName] = useState('');
    const [description, setDescription] = useState('');
    const [amount, setAmount] = useState('');
    const [loading, setLoading] = useState(false);

    const userId = user?.uid;

    const handleSubmit = async () => {
        if (!mealName.trim()) {
            showAlert('Error', 'Please enter a meal name');
            return;
        }
        if (!amount || parseFloat(amount) <= 0) {
            showAlert('Error', 'Please enter a valid amount in grams');
            return;
        }

        setLoading(true);
        try {
            await NutritionAPI.analyzeAndSave(userId, {
                name: mealName.trim(),
                desc: description.trim() || null,
                amnt: parseFloat(amount),
            });

            showAlert('Success', 'Meal logged and analyzed!', [
                { text: 'OK', onPress: () => router.back() },
            ]);
        } catch (err) {
            showAlert('Error', 'Failed to log meal. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={[
                    styles.scrollContent,
                    {
                        paddingTop: insets.top + spacing.md,
                        paddingBottom: insets.bottom + spacing.xl,
                        paddingHorizontal: pagePadding,
                        alignItems: 'center',
                    },
                ]}
                showsVerticalScrollIndicator={false}
                keyboardShouldPersistTaps="handled"
            >
                <View style={[styles.inner, cardMaxWidth ? { maxWidth: cardMaxWidth } : null]}>
                    <ScreenHeader title="Log Meal" isWeb={isWeb} />

                    {/* Info Card */}
                    <View style={styles.infoCard}>
                        <Ionicons name="sparkles" size={20} color={colors.neonPurple} />
                        <Text style={styles.infoText}>
                            Our AI will automatically analyze the nutritional content of your meal!
                        </Text>
                    </View>

                    {/* Form */}
                    <View style={styles.form}>
                        <Input
                            label="Meal Name"
                            value={mealName}
                            onChangeText={setMealName}
                            placeholder="e.g., Palak Paneer, Grilled Chicken"
                        />

                        <Input
                            label="Description (Optional)"
                            value={description}
                            onChangeText={setDescription}
                            placeholder="Describe ingredients or preparation..."
                            multiline
                            numberOfLines={3}
                        />

                        <Input
                            label="Amount (grams)"
                            value={amount}
                            onChangeText={setAmount}
                            placeholder="e.g., 200"
                            keyboardType="numeric"
                        />

                        <View style={styles.buttonContainer}>
                            <Button
                                title="Analyze & Save"
                                onPress={handleSubmit}
                                loading={loading}
                                icon={<Ionicons name="restaurant" size={20} color={colors.white} />}
                            />
                        </View>
                    </View>
                </View>
            </ScrollView>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    scrollView: {
        flex: 1,
        width: '100%',
    },
    scrollContent: {
        flexGrow: 1,
    },
    inner: {
        width: '100%',
    },
    infoCard: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        backgroundColor: colors.neonPurple + '15',
        padding: spacing.md,
        borderRadius: borderRadius.md,
        marginBottom: spacing.lg,
    },
    infoText: {
        ...typography.bodySmall,
        flex: 1,
        color: colors.inkPurple,
    },
    form: {
        gap: spacing.md,
    },
    buttonContainer: {
        marginTop: spacing.lg,
    },
});
