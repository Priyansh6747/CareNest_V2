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
import { NutritionAPI } from '../services/apiService';

export default function MealLog() {
    const router = useRouter();
    const { user } = useUser();

    const [mealName, setMealName] = useState('');
    const [description, setDescription] = useState('');
    const [amount, setAmount] = useState('');
    const [loading, setLoading] = useState(false);

    const userId = user?.uid;

    const handleSubmit = async () => {
        if (!mealName.trim()) {
            Alert.alert('Error', 'Please enter a meal name');
            return;
        }
        if (!amount || parseFloat(amount) <= 0) {
            Alert.alert('Error', 'Please enter a valid amount in grams');
            return;
        }

        setLoading(true);
        try {
            await NutritionAPI.analyzeAndSave(userId, {
                name: mealName.trim(),
                desc: description.trim() || null,
                amnt: parseFloat(amount),
            });

            Alert.alert('Success', 'Meal logged and analyzed!', [
                { text: 'OK', onPress: () => router.back() },
            ]);
        } catch (err) {
            Alert.alert('Error', 'Failed to log meal. Please try again.');
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
                        <Text style={styles.title}>Log Meal</Text>
                        <View style={{ width: 40 }} />
                    </View>

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
