import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    SafeAreaView,
    StatusBar,
    ActivityIndicator,
    Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useUser } from '../hooks/auth_context';
import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';
import { MealPlannerAPI, UserAPI, InsightsAPI } from '../services/apiService';

// Diet type options
const DIET_OPTIONS = [
    { id: 'veg', label: 'Vegetarian', icon: 'leaf', emoji: '🥬' },
    { id: 'non_veg', label: 'Non-Veg', icon: 'restaurant', emoji: '🍗' },
    { id: 'mixed', label: 'Mixed', icon: 'nutrition', emoji: '🍽️' },
];

// Duration options
const DURATION_OPTIONS = [
    { id: 'daily', label: 'Today\'s Plan', icon: 'today' },
    { id: 'weekly', label: 'Weekly Plan', icon: 'calendar' },
];

// Common allergies
const COMMON_ALLERGIES = [
    'Dairy', 'Nuts', 'Gluten', 'Eggs', 'Soy', 'Shellfish', 'Fish'
];

// Meal type icons and colors
const MEAL_ICONS = {
    'Breakfast': { icon: 'sunny', color: '#FF9800' },
    'Mid-Morning Snack': { icon: 'cafe', color: '#8D6E63' },
    'Lunch': { icon: 'restaurant', color: '#4CAF50' },
    'Evening Snack': { icon: 'ice-cream', color: '#E91E63' },
    'Dinner': { icon: 'moon', color: '#673AB7' },
    'Snack': { icon: 'fast-food', color: '#FF5722' },
};

export default function DietPlanner() {
    const router = useRouter();
    const { user } = useUser();

    // Form state
    const [age, setAge] = useState(25);
    const [pregnancyStage, setPregnancyStage] = useState('trimester_2');
    const [dietType, setDietType] = useState('mixed');
    const [selectedAllergies, setSelectedAllergies] = useState([]);
    const [nutrientFocus, setNutrientFocus] = useState([]);
    const [duration, setDuration] = useState('daily');

    // UI state
    const [loading, setLoading] = useState(false);
    const [mealPlan, setMealPlan] = useState(null);
    const [error, setError] = useState(null);
    const [showForm, setShowForm] = useState(true);

    const userId = user?.uid;

    useEffect(() => {
        loadUserPreferences();
    }, [userId]);

    const loadUserPreferences = async () => {
        if (!userId) return;

        try {
            // Load user profile for age, diet, allergies
            const profile = await UserAPI.getProfile(userId);
            if (profile) {
                if (profile.personal?.age) setAge(profile.personal.age);
                if (profile.diet?.diet_type) setDietType(profile.diet.diet_type);
                if (profile.diet?.allergies) setSelectedAllergies(profile.diet.allergies);
                if (profile.pregnancy?.stage) setPregnancyStage(profile.pregnancy.stage);
            }
        } catch (err) {
            console.log('Could not load profile preferences');
        }

        try {
            // Load priority nutrients from insights
            const insights = await InsightsAPI.getLatestInsights(userId);
            if (insights?.insights?.priority_nutrients) {
                const nutrients = insights.insights.priority_nutrients.map(n =>
                    n.replace(/_(mg|g|iu|mcg)$/i, '')
                );
                setNutrientFocus(nutrients.slice(0, 3));
            }
        } catch (err) {
            console.log('Could not load nutrient focus');
        }
    };

    const toggleAllergy = (allergy) => {
        setSelectedAllergies(prev =>
            prev.includes(allergy)
                ? prev.filter(a => a !== allergy)
                : [...prev, allergy]
        );
    };

    const generatePlan = async () => {
        setLoading(true);
        setError(null);
        setMealPlan(null);

        try {
            const result = await MealPlannerAPI.generateMealPlan({
                age,
                pregnancy_stage: pregnancyStage,
                diet_type: dietType,
                allergies: selectedAllergies,
                nutrient_focus: nutrientFocus,
                medical_conditions: [],
                meal_duration: duration,
                cultural_preference: 'indian',
            });

            if (result.success) {
                setMealPlan(result.meal_plan);
                setShowForm(false);
            } else {
                setError('Failed to generate meal plan');
            }
        } catch (err) {
            console.error('Meal plan error:', err);
            setError(err.message || 'Failed to generate meal plan. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const getMealIcon = (mealType) => {
        const config = MEAL_ICONS[mealType] || MEAL_ICONS['Snack'];
        return config;
    };

    const renderForm = () => (
        <View style={styles.formContainer}>
            {/* Diet Type Selection */}
            <Text style={styles.sectionLabel}>Diet Type</Text>
            <View style={styles.optionGrid}>
                {DIET_OPTIONS.map(option => (
                    <TouchableOpacity
                        key={option.id}
                        style={[
                            styles.optionCard,
                            dietType === option.id && styles.optionCardActive
                        ]}
                        onPress={() => setDietType(option.id)}
                    >
                        <Text style={styles.optionEmoji}>{option.emoji}</Text>
                        <Text style={[
                            styles.optionLabel,
                            dietType === option.id && styles.optionLabelActive
                        ]}>
                            {option.label}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>

            {/* Duration Selection */}
            <Text style={styles.sectionLabel}>Plan Duration</Text>
            <View style={styles.durationRow}>
                {DURATION_OPTIONS.map(option => (
                    <TouchableOpacity
                        key={option.id}
                        style={[
                            styles.durationChip,
                            duration === option.id && styles.durationChipActive
                        ]}
                        onPress={() => setDuration(option.id)}
                    >
                        <Ionicons
                            name={option.icon}
                            size={18}
                            color={duration === option.id ? colors.white : colors.neonPurple}
                        />
                        <Text style={[
                            styles.durationText,
                            duration === option.id && styles.durationTextActive
                        ]}>
                            {option.label}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>

            {/* Allergies */}
            <Text style={styles.sectionLabel}>Allergies to Avoid</Text>
            <View style={styles.allergyGrid}>
                {COMMON_ALLERGIES.map(allergy => (
                    <TouchableOpacity
                        key={allergy}
                        style={[
                            styles.allergyChip,
                            selectedAllergies.includes(allergy) && styles.allergyChipActive
                        ]}
                        onPress={() => toggleAllergy(allergy)}
                    >
                        <Text style={[
                            styles.allergyText,
                            selectedAllergies.includes(allergy) && styles.allergyTextActive
                        ]}>
                            {allergy}
                        </Text>
                        {selectedAllergies.includes(allergy) && (
                            <Ionicons name="close-circle" size={14} color={colors.white} />
                        )}
                    </TouchableOpacity>
                ))}
            </View>

            {/* Nutrient Focus Display */}
            {nutrientFocus.length > 0 && (
                <>
                    <Text style={styles.sectionLabel}>Focusing On (from your insights)</Text>
                    <View style={styles.nutrientRow}>
                        {nutrientFocus.map(n => (
                            <View key={n} style={styles.nutrientBadge}>
                                <Ionicons name="nutrition" size={14} color={colors.success} />
                                <Text style={styles.nutrientText}>{n}</Text>
                            </View>
                        ))}
                    </View>
                </>
            )}

            {/* Generate Button */}
            <TouchableOpacity
                style={styles.generateButton}
                onPress={generatePlan}
                disabled={loading}
            >
                <LinearGradient
                    colors={[colors.neonPurple, colors.mutedLavender]}
                    style={styles.generateButtonGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                >
                    {loading ? (
                        <ActivityIndicator color={colors.white} size="small" />
                    ) : (
                        <>
                            <Ionicons name="sparkles" size={20} color={colors.white} />
                            <Text style={styles.generateButtonText}>
                                Generate AI Meal Plan
                            </Text>
                        </>
                    )}
                </LinearGradient>
            </TouchableOpacity>

            {loading && (
                <Text style={styles.loadingHint}>
                    Creating your personalized meal plan... This may take a moment.
                </Text>
            )}
        </View>
    );

    const renderMealPlan = () => {
        if (!mealPlan) return null;

        const days = mealPlan.days || [];
        const tips = mealPlan.tips || [];

        return (
            <View style={styles.planContainer}>
                {/* Summary */}
                {mealPlan.plan_summary && (
                    <Card style={styles.summaryCard}>
                        <Ionicons name="sparkles" size={20} color={colors.neonPurple} />
                        <Text style={styles.summaryText}>{mealPlan.plan_summary}</Text>
                    </Card>
                )}

                {/* Edit Button */}
                <TouchableOpacity
                    style={styles.editButton}
                    onPress={() => setShowForm(true)}
                >
                    <Ionicons name="create-outline" size={16} color={colors.neonPurple} />
                    <Text style={styles.editButtonText}>Edit Preferences</Text>
                </TouchableOpacity>

                {/* Days */}
                {days.map((day, dayIndex) => (
                    <View key={dayIndex} style={styles.dayContainer}>
                        <Text style={styles.dayTitle}>{day.day}</Text>
                        
                        {day.meals?.map((meal, mealIndex) => {
                            const iconConfig = getMealIcon(meal.type);
                            return (
                                <Card key={mealIndex} style={styles.mealCard}>
                                    <View style={styles.mealHeader}>
                                        <View style={[styles.mealIcon, { backgroundColor: iconConfig.color + '20' }]}>
                                            <Ionicons
                                                name={iconConfig.icon}
                                                size={20}
                                                color={iconConfig.color}
                                            />
                                        </View>
                                        <View style={styles.mealInfo}>
                                            <Text style={styles.mealType}>{meal.type}</Text>
                                            <Text style={styles.mealName}>{meal.name}</Text>
                                        </View>
                                        {meal.calories_approx && (
                                            <View style={styles.caloriesBadge}>
                                                <Text style={styles.caloriesText}>
                                                    {meal.calories_approx} cal
                                                </Text>
                                            </View>
                                        )}
                                    </View>

                                    {meal.description && (
                                        <Text style={styles.mealDescription}>{meal.description}</Text>
                                    )}

                                    {meal.items && meal.items.length > 0 && (
                                        <View style={styles.itemsContainer}>
                                            {meal.items.map((item, i) => (
                                                <Text key={i} style={styles.itemText}>• {item}</Text>
                                            ))}
                                        </View>
                                    )}

                                    {meal.nutrients && meal.nutrients.length > 0 && (
                                        <View style={styles.nutrientTags}>
                                            {meal.nutrients.slice(0, 3).map((n, i) => (
                                                <View key={i} style={styles.nutrientTag}>
                                                    <Text style={styles.nutrientTagText}>{n}</Text>
                                                </View>
                                            ))}
                                        </View>
                                    )}
                                </Card>
                            );
                        })}

                        {day.total_calories && (
                            <Text style={styles.dayCalories}>
                                Total: ~{day.total_calories} calories
                            </Text>
                        )}
                    </View>
                ))}

                {/* Tips */}
                {tips.length > 0 && (
                    <Card style={styles.tipsCard}>
                        <View style={styles.tipsHeader}>
                            <Ionicons name="bulb" size={20} color={colors.warning} />
                            <Text style={styles.tipsTitle}>Tips</Text>
                        </View>
                        {tips.map((tip, i) => (
                            <Text key={i} style={styles.tipText}>• {tip}</Text>
                        ))}
                    </Card>
                )}

                {/* Foods to Avoid */}
                {mealPlan.foods_to_avoid?.length > 0 && (
                    <Card style={styles.avoidCard}>
                        <View style={styles.avoidHeader}>
                            <Ionicons name="warning" size={18} color={colors.error} />
                            <Text style={styles.avoidTitle}>Foods to Avoid</Text>
                        </View>
                        <Text style={styles.avoidText}>
                            {mealPlan.foods_to_avoid.join(', ')}
                        </Text>
                    </Card>
                )}
            </View>
        );
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
                        <Text style={styles.title}>Diet Planner</Text>
                        <View style={{ width: 40 }} />
                    </View>

                    {/* Intro Card */}
                    <Card style={styles.introCard}>
                        <View style={styles.introContent}>
                            <Text style={styles.introEmoji}>🍽️</Text>
                            <View style={styles.introText}>
                                <Text style={styles.introTitle}>AI-Powered Meal Plans</Text>
                                <Text style={styles.introDesc}>
                                    Get personalized meal suggestions based on your pregnancy stage and nutritional needs
                                </Text>
                            </View>
                        </View>
                    </Card>

                    {/* Error State */}
                    {error && (
                        <Card style={styles.errorCard}>
                            <Ionicons name="alert-circle" size={24} color={colors.error} />
                            <Text style={styles.errorText}>{error}</Text>
                            <TouchableOpacity onPress={() => setError(null)}>
                                <Text style={styles.retryText}>Dismiss</Text>
                            </TouchableOpacity>
                        </Card>
                    )}

                    {/* Form or Plan */}
                    {showForm ? renderForm() : renderMealPlan()}

                    <View style={{ height: spacing.xxl }} />
                </ScrollView>
            </SafeAreaView>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    safeArea: { flex: 1 },
    scrollView: { flex: 1 },
    scrollContent: { padding: spacing.lg },
    
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: spacing.lg,
        marginTop: spacing.md,
    },
    backButton: { padding: spacing.sm },
    title: { ...typography.h2 },

    introCard: {
        padding: spacing.lg,
        marginBottom: spacing.lg,
    },
    introContent: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    introEmoji: { fontSize: 40, marginRight: spacing.md },
    introText: { flex: 1 },
    introTitle: { ...typography.h3, marginBottom: spacing.xs },
    introDesc: { ...typography.bodySmall },

    formContainer: { marginBottom: spacing.lg },
    sectionLabel: {
        ...typography.body,
        fontWeight: '600',
        marginBottom: spacing.sm,
        marginTop: spacing.md,
    },

    optionGrid: {
        flexDirection: 'row',
        gap: spacing.sm,
    },
    optionCard: {
        flex: 1,
        backgroundColor: colors.white,
        borderRadius: borderRadius.md,
        padding: spacing.md,
        alignItems: 'center',
        borderWidth: 2,
        borderColor: colors.lightOrchid,
    },
    optionCardActive: {
        borderColor: colors.neonPurple,
        backgroundColor: colors.neonPurple + '10',
    },
    optionEmoji: { fontSize: 28, marginBottom: spacing.xs },
    optionLabel: { ...typography.caption, fontWeight: '600' },
    optionLabelActive: { color: colors.neonPurple },

    durationRow: {
        flexDirection: 'row',
        gap: spacing.sm,
    },
    durationChip: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: spacing.xs,
        paddingVertical: spacing.md,
        backgroundColor: colors.white,
        borderRadius: borderRadius.md,
        borderWidth: 1,
        borderColor: colors.lightOrchid,
    },
    durationChipActive: {
        backgroundColor: colors.neonPurple,
        borderColor: colors.neonPurple,
    },
    durationText: { ...typography.bodySmall, color: colors.neonPurple },
    durationTextActive: { color: colors.white },

    allergyGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
    },
    allergyChip: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        backgroundColor: colors.white,
        borderRadius: borderRadius.full,
        borderWidth: 1,
        borderColor: colors.lightOrchid,
    },
    allergyChipActive: {
        backgroundColor: colors.error,
        borderColor: colors.error,
    },
    allergyText: { ...typography.caption },
    allergyTextActive: { color: colors.white },

    nutrientRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
    },
    nutrientBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        backgroundColor: colors.success + '15',
        borderRadius: borderRadius.sm,
    },
    nutrientText: {
        ...typography.caption,
        color: colors.success,
        textTransform: 'capitalize',
    },

    generateButton: {
        marginTop: spacing.xl,
        borderRadius: borderRadius.md,
        overflow: 'hidden',
    },
    generateButtonGradient: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: spacing.sm,
        paddingVertical: spacing.lg,
    },
    generateButtonText: {
        ...typography.button,
        fontSize: 18,
    },
    loadingHint: {
        ...typography.caption,
        textAlign: 'center',
        marginTop: spacing.md,
        fontStyle: 'italic',
    },

    errorCard: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        padding: spacing.md,
        backgroundColor: colors.error + '15',
        marginBottom: spacing.lg,
    },
    errorText: { ...typography.bodySmall, color: colors.error, flex: 1 },
    retryText: { ...typography.bodySmall, color: colors.neonPurple },

    planContainer: {},
    summaryCard: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: spacing.sm,
        padding: spacing.lg,
        marginBottom: spacing.md,
    },
    summaryText: { ...typography.body, flex: 1 },

    editButton: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        alignSelf: 'flex-end',
        marginBottom: spacing.md,
    },
    editButtonText: { ...typography.bodySmall, color: colors.neonPurple },

    dayContainer: { marginBottom: spacing.lg },
    dayTitle: { ...typography.h3, marginBottom: spacing.md },

    mealCard: { padding: spacing.md, marginBottom: spacing.sm },
    mealHeader: { flexDirection: 'row', alignItems: 'center' },
    mealIcon: {
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
    },
    mealInfo: { flex: 1, marginLeft: spacing.sm },
    mealType: { ...typography.caption },
    mealName: { ...typography.body, fontWeight: '600' },
    caloriesBadge: {
        backgroundColor: colors.lightOrchid,
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.sm,
    },
    caloriesText: { ...typography.caption, fontWeight: '600' },
    mealDescription: {
        ...typography.bodySmall,
        marginTop: spacing.sm,
        color: colors.mutedPurple,
    },
    itemsContainer: { marginTop: spacing.sm },
    itemText: { ...typography.bodySmall, marginBottom: 2 },
    nutrientTags: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.xs,
        marginTop: spacing.sm,
    },
    nutrientTag: {
        backgroundColor: colors.success + '20',
        paddingHorizontal: spacing.sm,
        paddingVertical: 2,
        borderRadius: borderRadius.sm,
    },
    nutrientTagText: {
        ...typography.caption,
        color: colors.success,
        textTransform: 'capitalize',
    },
    dayCalories: {
        ...typography.bodySmall,
        textAlign: 'right',
        color: colors.dustyPurple,
        marginTop: spacing.sm,
    },

    tipsCard: { padding: spacing.lg, marginBottom: spacing.md },
    tipsHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        marginBottom: spacing.sm,
    },
    tipsTitle: { ...typography.h3 },
    tipText: { ...typography.bodySmall, marginBottom: spacing.xs },

    avoidCard: {
        padding: spacing.md,
        backgroundColor: colors.error + '10',
    },
    avoidHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        marginBottom: spacing.xs,
    },
    avoidTitle: { ...typography.bodySmall, fontWeight: '600', color: colors.error },
    avoidText: { ...typography.caption },
});
