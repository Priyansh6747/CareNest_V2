import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    SafeAreaView,
    StatusBar,
    Linking,
    Platform,
    Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';

import { useUser } from '../hooks/auth_context';
import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius, shadows } from '../theme';
import { FoodOutletAPI, InsightsAPI, UserAPI } from '../services/apiService';

const CATEGORIES = [
    { id: 'all', label: 'All', icon: 'restaurant' },
    { id: 'restaurant', label: 'Restaurant', icon: 'restaurant-outline' },
    { id: 'grocery', label: 'Grocery', icon: 'cart-outline' },
    { id: 'organic', label: 'Organic', icon: 'leaf-outline' },
    { id: 'cafe', label: 'Cafe', icon: 'cafe-outline' },
];

// Food tags for dietary filtering
// Tags: veg, nonveg, dairy, eggs, fish, nuts, gluten, soy, shellfish
const NUTRIENT_FOOD_MAP = {
    iron: {
        name: 'Iron',
        icon: 'fitness',
        color: '#E53935',
        foods: [
            { name: 'Spinach', emoji: '🥬', benefit: 'Rich in non-heme iron', tags: ['veg'] },
            { name: 'Red Meat', emoji: '🥩', benefit: 'Heme iron, easily absorbed', tags: ['nonveg'] },
            { name: 'Lentils (Dal)', emoji: '🫘', benefit: '3.3mg per 100g', tags: ['veg'] },
            { name: 'Chickpeas', emoji: '🧆', benefit: 'Great vegetarian source', tags: ['veg'] },
            { name: 'Tofu', emoji: '🧊', benefit: 'Plant-based iron', tags: ['veg', 'soy'] },
            { name: 'Jaggery (Gud)', emoji: '🍬', benefit: 'Traditional iron source', tags: ['veg'] },
            { name: 'Dates', emoji: '🫘', benefit: 'Sweet iron boost', tags: ['veg'] },
            { name: 'Pomegranate', emoji: '🍎', benefit: 'Iron + Vitamin C', tags: ['veg'] },
        ],
        tip: 'Pair with Vitamin C rich foods for better absorption',
    },
    calcium: {
        name: 'Calcium',
        icon: 'body',
        color: '#1E88E5',
        foods: [
            { name: 'Milk', emoji: '🥛', benefit: '125mg per 100ml', tags: ['veg', 'dairy'] },
            { name: 'Paneer', emoji: '🧀', benefit: 'Rich in calcium & protein', tags: ['veg', 'dairy'] },
            { name: 'Yogurt (Dahi)', emoji: '🥣', benefit: 'Probiotic + calcium', tags: ['veg', 'dairy'] },
            { name: 'Ragi', emoji: '🌾', benefit: '344mg per 100g', tags: ['veg'] },
            { name: 'Sesame Seeds', emoji: '🌱', benefit: 'Til ladoo recommended', tags: ['veg'] },
            { name: 'Broccoli', emoji: '🥦', benefit: 'Plant-based calcium', tags: ['veg'] },
            { name: 'Almonds', emoji: '🌰', benefit: '264mg per 100g', tags: ['veg', 'nuts'] },
            { name: 'Sardines', emoji: '🐟', benefit: 'With bones, 382mg', tags: ['nonveg', 'fish'] },
        ],
        tip: 'Vitamin D helps calcium absorption - get some sunlight!',
    },
    protein: {
        name: 'Protein',
        icon: 'barbell',
        color: '#7B1FA2',
        foods: [
            { name: 'Eggs', emoji: '🥚', benefit: '13g per 2 eggs', tags: ['veg', 'eggs'] },
            { name: 'Chicken', emoji: '🍗', benefit: '27g per 100g', tags: ['nonveg'] },
            { name: 'Fish', emoji: '🐟', benefit: 'Omega-3 + protein', tags: ['nonveg', 'fish'] },
            { name: 'Paneer', emoji: '🧀', benefit: '18g per 100g', tags: ['veg', 'dairy'] },
            { name: 'Moong Dal', emoji: '🫘', benefit: '24g per 100g', tags: ['veg'] },
            { name: 'Greek Yogurt', emoji: '🥣', benefit: 'Double the protein', tags: ['veg', 'dairy'] },
            { name: 'Soy Chunks', emoji: '🫘', benefit: '52g per 100g', tags: ['veg', 'soy'] },
            { name: 'Quinoa', emoji: '🌾', benefit: 'Complete protein', tags: ['veg'] },
        ],
        tip: 'Aim for protein in every meal during pregnancy',
    },
    folate: {
        name: 'Folate',
        icon: 'leaf',
        color: '#43A047',
        foods: [
            { name: 'Leafy Greens', emoji: '🥬', benefit: 'Spinach, methi, palak', tags: ['veg'] },
            { name: 'Oranges', emoji: '🍊', benefit: 'Natural folate source', tags: ['veg'] },
            { name: 'Lentils', emoji: '🫘', benefit: '181mcg per cup', tags: ['veg'] },
            { name: 'Avocado', emoji: '🥑', benefit: '90mcg per avocado', tags: ['veg'] },
            { name: 'Fortified Cereals', emoji: '🥣', benefit: 'Check labels', tags: ['veg', 'gluten'] },
            { name: 'Beetroot', emoji: '🫓', benefit: 'Great in salads', tags: ['veg'] },
            { name: 'Asparagus', emoji: '🥒', benefit: '134mcg per cup', tags: ['veg'] },
        ],
        tip: 'Critical for baby\'s neural development in first trimester',
    },
    folic_acid: {
        name: 'Folic Acid',
        icon: 'leaf',
        color: '#43A047',
        foods: [
            { name: 'Leafy Greens', emoji: '🥬', benefit: 'Spinach, methi, palak', tags: ['veg'] },
            { name: 'Oranges', emoji: '🍊', benefit: 'Natural folate source', tags: ['veg'] },
            { name: 'Lentils', emoji: '🫘', benefit: '181mcg per cup', tags: ['veg'] },
            { name: 'Avocado', emoji: '🥑', benefit: '90mcg per avocado', tags: ['veg'] },
            { name: 'Fortified Cereals', emoji: '🥣', benefit: 'Check labels', tags: ['veg', 'gluten'] },
            { name: 'Beetroot', emoji: '🫓', benefit: 'Great in salads', tags: ['veg'] },
        ],
        tip: 'Critical for baby\'s neural development in first trimester',
    },
    omega_3: {
        name: 'Omega-3',
        icon: 'water',
        color: '#00ACC1',
        foods: [
            { name: 'Salmon', emoji: '🐟', benefit: 'DHA & EPA rich', tags: ['nonveg', 'fish'] },
            { name: 'Walnuts', emoji: '🌰', benefit: 'Plant-based omega-3', tags: ['veg', 'nuts'] },
            { name: 'Flaxseeds', emoji: '🌱', benefit: 'Add to smoothies', tags: ['veg'] },
            { name: 'Chia Seeds', emoji: '🫘', benefit: '5g omega-3 per oz', tags: ['veg'] },
            { name: 'Sardines', emoji: '🐟', benefit: 'Low mercury option', tags: ['nonveg', 'fish'] },
            { name: 'Mustard Oil', emoji: '🫒', benefit: 'Cook with it', tags: ['veg'] },
            { name: 'Hemp Seeds', emoji: '🌱', benefit: 'Complete protein too', tags: ['veg'] },
        ],
        tip: 'Essential for baby\'s brain development',
    },
    vitamin_d: {
        name: 'Vitamin D',
        icon: 'sunny',
        color: '#FFB300',
        foods: [
            { name: 'Egg Yolks', emoji: '🥚', benefit: 'Natural D3 source', tags: ['veg', 'eggs'] },
            { name: 'Fatty Fish', emoji: '🐟', benefit: 'Salmon, mackerel', tags: ['nonveg', 'fish'] },
            { name: 'Fortified Milk', emoji: '🥛', benefit: 'Check labels', tags: ['veg', 'dairy'] },
            { name: 'Mushrooms', emoji: '🍄', benefit: 'Sun-exposed varieties', tags: ['veg'] },
            { name: 'Fortified Cereals', emoji: '🥣', benefit: 'Check labels', tags: ['veg', 'gluten'] },
            { name: 'Fortified Orange Juice', emoji: '🍊', benefit: 'Dairy-free option', tags: ['veg'] },
        ],
        tip: '15-20 minutes of morning sunlight helps too!',
    },
    fiber: {
        name: 'Fiber',
        icon: 'nutrition',
        color: '#8D6E63',
        foods: [
            { name: 'Oats', emoji: '🥣', benefit: '10g per 100g', tags: ['veg', 'gluten'] },
            { name: 'Whole Wheat', emoji: '🌾', benefit: 'Roti, bread', tags: ['veg', 'gluten'] },
            { name: 'Fruits', emoji: '🍎', benefit: 'Apple, pear with skin', tags: ['veg'] },
            { name: 'Vegetables', emoji: '🥕', benefit: 'Carrots, beans', tags: ['veg'] },
            { name: 'Rajma', emoji: '🫘', benefit: '25g per cup', tags: ['veg'] },
            { name: 'Chia Seeds', emoji: '🌱', benefit: 'Soak before eating', tags: ['veg'] },
            { name: 'Quinoa', emoji: '🌾', benefit: 'Gluten-free option', tags: ['veg'] },
        ],
        tip: 'Helps prevent pregnancy constipation',
    },
    zinc: {
        name: 'Zinc',
        icon: 'shield-checkmark',
        color: '#5D4037',
        foods: [
            { name: 'Pumpkin Seeds', emoji: '🎃', benefit: '7.5mg per 100g', tags: ['veg'] },
            { name: 'Chickpeas', emoji: '🧆', benefit: 'Great zinc source', tags: ['veg'] },
            { name: 'Cashews', emoji: '🥜', benefit: 'Snack on these', tags: ['veg', 'nuts'] },
            { name: 'Paneer', emoji: '🧀', benefit: 'Dairy zinc', tags: ['veg', 'dairy'] },
            { name: 'Eggs', emoji: '🥚', benefit: 'Easy to include daily', tags: ['veg', 'eggs'] },
            { name: 'Lentils', emoji: '🫘', benefit: '4.8mg per cup', tags: ['veg'] },
            { name: 'Oysters', emoji: '🦪', benefit: 'Highest zinc food', tags: ['nonveg', 'shellfish'] },
        ],
        tip: 'Important for immune system and growth',
    },
    vitamin_c: {
        name: 'Vitamin C',
        icon: 'flash',
        color: '#FF7043',
        foods: [
            { name: 'Oranges', emoji: '🍊', benefit: '70mg per fruit', tags: ['veg'] },
            { name: 'Amla', emoji: '🫐', benefit: 'Indian superfood', tags: ['veg'] },
            { name: 'Bell Peppers', emoji: '🫑', benefit: 'More than oranges!', tags: ['veg'] },
            { name: 'Guava', emoji: '🍈', benefit: '228mg per fruit', tags: ['veg'] },
            { name: 'Lemon', emoji: '🍋', benefit: 'Add to water', tags: ['veg'] },
            { name: 'Tomatoes', emoji: '🍅', benefit: 'Raw or cooked', tags: ['veg'] },
            { name: 'Papaya', emoji: '🍈', benefit: 'Ripe only in pregnancy', tags: ['veg'] },
        ],
        tip: 'Helps iron absorption - pair with iron-rich foods',
    },
};

// Allergy/condition to food tag mapping
const ALLERGY_TAG_MAP = {
    'lactose': ['dairy'],
    'lactose intolerant': ['dairy'],
    'dairy': ['dairy'],
    'milk': ['dairy'],
    'nuts': ['nuts'],
    'nut allergy': ['nuts'],
    'tree nuts': ['nuts'],
    'peanut': ['nuts'],
    'gluten': ['gluten'],
    'celiac': ['gluten'],
    'wheat': ['gluten'],
    'eggs': ['eggs'],
    'egg': ['eggs'],
    'fish': ['fish'],
    'seafood': ['fish', 'shellfish'],
    'shellfish': ['shellfish'],
    'soy': ['soy'],
    'soya': ['soy'],
};

export default function FoodOutlets() {
    const router = useRouter();
    const { user } = useUser();

    const [outlets, setOutlets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [location, setLocation] = useState(null);
    const [priorityNutrients, setPriorityNutrients] = useState(null);
    const [nutrientTips, setNutrientTips] = useState(null);
    
    // User dietary preferences
    const [userDietPrefs, setUserDietPrefs] = useState({
        dietType: 'mixed', // veg, non_veg, mixed
        allergies: [],     // e.g., ['dairy', 'nuts', 'gluten']
        conditions: [],    // e.g., ['gestational_diabetes']
    });

    const userId = user?.uid;

    // Filter foods based on user's dietary preferences
    const filterFoodsForUser = (foods) => {
        if (!foods) return [];
        
        // Get excluded tags based on allergies
        const excludedTags = new Set();
        
        // Add allergy-based exclusions
        userDietPrefs.allergies.forEach(allergy => {
            const allergyLower = allergy.toLowerCase();
            // Check direct mapping
            if (ALLERGY_TAG_MAP[allergyLower]) {
                ALLERGY_TAG_MAP[allergyLower].forEach(tag => excludedTags.add(tag));
            }
            // Also check if the allergy itself is a tag
            if (['dairy', 'nuts', 'gluten', 'eggs', 'fish', 'soy', 'shellfish'].includes(allergyLower)) {
                excludedTags.add(allergyLower);
            }
        });
        
        // Filter based on diet type
        const isVeg = userDietPrefs.dietType === 'veg';
        
        return foods.filter(food => {
            const tags = food.tags || [];
            
            // If vegetarian, exclude non-veg foods
            if (isVeg && tags.includes('nonveg')) {
                return false;
            }
            
            // Exclude foods matching any excluded allergen tags
            if (tags.some(tag => excludedTags.has(tag))) {
                return false;
            }
            
            return true;
        });
    };

    useEffect(() => {
        initializeData();
    }, [userId]);

    useEffect(() => {
        if (location) {
            loadOutlets();
        }
    }, [location, selectedCategory]);

    const initializeData = async () => {
        // Get user's location
        try {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                setError('Location permission is required to find nearby food outlets');
                setLoading(false);
                return;
            }

            const loc = await Location.getCurrentPositionAsync({});
            setLocation({
                lat: loc.coords.latitude,
                lng: loc.coords.longitude,
            });
        } catch (err) {
            setError('Failed to get your location');
            setLoading(false);
            return;
        }

        // Try to get user dietary preferences and insights
        if (userId) {
            // Fetch user profile for dietary preferences (primary source)
            try {
                const profile = await UserAPI.getProfile(userId);
                if (profile) {
                    setUserDietPrefs({
                        dietType: profile.diet?.diet_type || 'mixed',
                        allergies: profile.diet?.allergies || [],
                        conditions: profile.pregnancy?.known_conditions || [],
                    });
                    console.log('Loaded diet prefs:', profile.diet);
                }
            } catch (profileErr) {
                console.log('Could not load user profile, using defaults');
            }
            
            // Fetch insights for priority nutrients
            try {
                const insights = await InsightsAPI.getLatestInsights(userId);
                if (insights?.insights?.priority_nutrients) {
                    // Clean nutrient names
                    const cleaned = insights.insights.priority_nutrients.map(n => 
                        n.replace(/_(mg|g|iu|mcg)$/i, '')
                    );
                    setPriorityNutrients(cleaned);
                }
            } catch (err) {
                console.log('No insights for food recommendations');
            }
        }
    };

    const loadOutlets = async () => {
        if (!location) return;

        setLoading(true);
        setError(null);

        try {
            const data = await FoodOutletAPI.findNearbyOutlets({
                lat: location.lat,
                lng: location.lng,
                radius: 3000,
                limit: 15,
                category: selectedCategory,
                priority_nutrients: priorityNutrients,
            });

            setOutlets(data.outlets || []);
            if (data.nutrient_recommendations) {
                setNutrientTips(data.nutrient_recommendations);
            }
        } catch (err) {
            console.log('Failed to load outlets:', err);
            setError('Failed to find nearby food outlets');
        } finally {
            setLoading(false);
        }
    };

    const openMaps = (outlet) => {
        const { lat, lng } = outlet.location;
        const label = encodeURIComponent(outlet.name);
        
        const url = Platform.select({
            ios: `maps:0,0?q=${label}@${lat},${lng}`,
            android: `geo:0,0?q=${lat},${lng}(${label})`,
        });

        Linking.canOpenURL(url).then(supported => {
            if (supported) {
                Linking.openURL(url);
            } else {
                // Fallback to Google Maps web
                Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${lat},${lng}`);
            }
        });
    };

    const getCategoryIcon = (category) => {
        switch (category) {
            case 'grocery':
                return 'cart';
            case 'cafe':
                return 'cafe';
            case 'bakery':
                return 'pizza';
            case 'organic':
                return 'leaf';
            default:
                return 'restaurant';
        }
    };

    const getCategoryColor = (category) => {
        switch (category) {
            case 'grocery':
                return colors.softBlue;
            case 'cafe':
                return colors.warning;
            case 'organic':
                return colors.success;
            case 'bakery':
                return colors.dustyPurple;
            default:
                return colors.neonPurple;
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
                        <Text style={styles.title}>Healthy Food</Text>
                        <TouchableOpacity onPress={loadOutlets} style={styles.refreshButton}>
                            <Ionicons name="refresh" size={24} color={colors.neonPurple} />
                        </TouchableOpacity>
                    </View>

                    {/* Category Filters */}
                    <ScrollView
                        horizontal
                        showsHorizontalScrollIndicator={false}
                        style={styles.categoriesScroll}
                        contentContainerStyle={styles.categoriesContent}
                    >
                        {CATEGORIES.map(cat => (
                            <TouchableOpacity
                                key={cat.id}
                                style={[
                                    styles.categoryChip,
                                    selectedCategory === cat.id && styles.categoryChipActive
                                ]}
                                onPress={() => setSelectedCategory(cat.id)}
                            >
                                <Ionicons
                                    name={cat.icon}
                                    size={16}
                                    color={selectedCategory === cat.id ? colors.white : colors.neonPurple}
                                />
                                <Text style={[
                                    styles.categoryText,
                                    selectedCategory === cat.id && styles.categoryTextActive
                                ]}>
                                    {cat.label}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </ScrollView>

                    {/* Nutrient Tips Banner */}
                    {priorityNutrients && priorityNutrients.length > 0 && (
                        <Card style={styles.tipsBanner}>
                            <View style={styles.tipsHeader}>
                                <Ionicons name="bulb" size={20} color={colors.warning} />
                                <Text style={styles.tipsTitle}>Based on your nutrition needs</Text>
                            </View>
                            <Text style={styles.tipsText}>
                                Looking for places with foods rich in: {priorityNutrients.slice(0, 3).join(', ')}
                            </Text>
                        </Card>
                    )}

                    {/* Foods to Boost Your Nutrients Section */}
                    {priorityNutrients && priorityNutrients.length > 0 && (
                        <View style={styles.foodSuggestionsSection}>
                            <Text style={styles.sectionTitle}>
                                🍽️ Foods to Boost Your Nutrients
                            </Text>
                            <Text style={styles.sectionSubtitle}>
                                Include these in your diet to meet your nutritional needs
                            </Text>

                            {priorityNutrients.slice(0, 4).map((nutrient, index) => {
                                const nutrientKey = nutrient.toLowerCase().replace(/\s+/g, '_');
                                const nutrientData = NUTRIENT_FOOD_MAP[nutrientKey];
                                
                                if (!nutrientData) return null;

                                // Filter foods based on user dietary preferences
                                const filteredFoods = filterFoodsForUser(nutrientData.foods);
                                
                                // Skip this nutrient card if no foods available after filtering
                                if (filteredFoods.length === 0) return null;

                                return (
                                    <Card key={index} style={styles.nutrientFoodCard}>
                                        {/* Nutrient Header */}
                                        <View style={styles.nutrientHeader}>
                                            <View style={[
                                                styles.nutrientIconContainer,
                                                { backgroundColor: nutrientData.color + '20' }
                                            ]}>
                                                <Ionicons 
                                                    name={nutrientData.icon} 
                                                    size={20} 
                                                    color={nutrientData.color} 
                                                />
                                            </View>
                                            <View style={styles.nutrientTitleContainer}>
                                                <Text style={styles.nutrientName}>{nutrientData.name}</Text>
                                                <Text style={styles.nutrientLabel}>You need more of this</Text>
                                            </View>
                                            {/* Diet preference badge */}
                                            {userDietPrefs.dietType === 'veg' && (
                                                <View style={styles.dietBadge}>
                                                    <Text style={styles.dietBadgeText}>🌱 Veg</Text>
                                                </View>
                                            )}
                                        </View>

                                        {/* Food Grid - now filtered */}
                                        <View style={styles.foodGrid}>
                                            {filteredFoods.slice(0, 6).map((food, foodIndex) => (
                                                <View key={foodIndex} style={styles.foodItem}>
                                                    <Text style={styles.foodEmoji}>{food.emoji}</Text>
                                                    <Text style={styles.foodName}>{food.name}</Text>
                                                    <Text style={styles.foodBenefit}>{food.benefit}</Text>
                                                </View>
                                            ))}
                                        </View>

                                        {/* Show if some foods were filtered */}
                                        {filteredFoods.length < nutrientData.foods.length && (
                                            <Text style={styles.filteredNote}>
                                                Showing {filteredFoods.length} of {nutrientData.foods.length} foods based on your dietary preferences
                                            </Text>
                                        )}

                                        {/* Tip */}
                                        <View style={styles.nutrientTip}>
                                            <Ionicons name="information-circle" size={14} color={colors.dustyPurple} />
                                            <Text style={styles.nutrientTipText}>{nutrientData.tip}</Text>
                                        </View>
                                    </Card>
                                );
                            })}
                        </View>
                    )}

                    {/* Section Divider */}
                    {priorityNutrients && priorityNutrients.length > 0 && !loading && outlets.length > 0 && (
                        <View style={styles.sectionDivider}>
                            <View style={styles.dividerLine} />
                            <Text style={styles.dividerText}>Nearby Places</Text>
                            <View style={styles.dividerLine} />
                        </View>
                    )}

                    {/* Loading State */}
                    {loading && (
                        <Card style={styles.loadingCard}>
                            <Ionicons name="restaurant" size={40} color={colors.dustyPurple} />
                            <Text style={styles.loadingText}>Finding healthy food options nearby...</Text>
                        </Card>
                    )}

                    {/* Error State */}
                    {error && !loading && (
                        <Card style={styles.errorCard}>
                            <Ionicons name="alert-circle" size={40} color={colors.error} />
                            <Text style={styles.errorText}>{error}</Text>
                            <TouchableOpacity style={styles.retryButton} onPress={initializeData}>
                                <Text style={styles.retryText}>Try Again</Text>
                            </TouchableOpacity>
                        </Card>
                    )}

                    {/* Outlets List */}
                    {!loading && !error && outlets.length === 0 && (
                        <Card style={styles.emptyCard}>
                            <Ionicons name="search" size={40} color={colors.dustyPurple} />
                            <Text style={styles.emptyTitle}>No outlets found</Text>
                            <Text style={styles.emptyText}>
                                Try expanding your search or changing the category
                            </Text>
                        </Card>
                    )}

                    {!loading && !error && outlets.map((outlet, index) => (
                        <TouchableOpacity
                            key={index}
                            activeOpacity={0.8}
                            onPress={() => openMaps(outlet)}
                        >
                            <Card style={styles.outletCard}>
                                <View style={styles.outletHeader}>
                                    <View style={[
                                        styles.outletIcon,
                                        { backgroundColor: getCategoryColor(outlet.category) + '20' }
                                    ]}>
                                        <Ionicons
                                            name={getCategoryIcon(outlet.category)}
                                            size={24}
                                            color={getCategoryColor(outlet.category)}
                                        />
                                    </View>
                                    <View style={styles.outletInfo}>
                                        <Text style={styles.outletName}>{outlet.name}</Text>
                                        <Text style={styles.outletCategory}>
                                            {outlet.category.charAt(0).toUpperCase() + outlet.category.slice(1)}
                                        </Text>
                                    </View>
                                    <Ionicons name="navigate" size={20} color={colors.neonPurple} />
                                </View>

                                <Text style={styles.outletAddress}>{outlet.address}</Text>

                                {outlet.distance_meters && (
                                    <View style={styles.distanceBadge}>
                                        <Ionicons name="location" size={14} color={colors.dustyPurple} />
                                        <Text style={styles.distanceText}>
                                            {outlet.distance_meters < 1000
                                                ? `${Math.round(outlet.distance_meters)}m away`
                                                : `${(outlet.distance_meters / 1000).toFixed(1)}km away`}
                                        </Text>
                                    </View>
                                )}

                                {outlet.nutrient_match && outlet.nutrient_match.length > 0 && (
                                    <View style={styles.nutrientMatch}>
                                        <Ionicons name="nutrition" size={14} color={colors.success} />
                                        <Text style={styles.nutrientMatchText}>
                                            {outlet.recommendation || `Good for: ${outlet.nutrient_match.join(', ')}`}
                                        </Text>
                                    </View>
                                )}
                            </Card>
                        </TouchableOpacity>
                    ))}

                    {/* Bottom spacer */}
                    <View style={{ height: spacing.xxl }} />
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
    refreshButton: {
        padding: spacing.sm,
    },
    title: {
        ...typography.h2,
    },
    categoriesScroll: {
        marginBottom: spacing.lg,
    },
    categoriesContent: {
        gap: spacing.sm,
    },
    categoryChip: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.full,
        backgroundColor: colors.white,
        borderWidth: 1,
        borderColor: colors.lightOrchid,
    },
    categoryChipActive: {
        backgroundColor: colors.neonPurple,
        borderColor: colors.neonPurple,
    },
    categoryText: {
        ...typography.bodySmall,
        color: colors.neonPurple,
    },
    categoryTextActive: {
        color: colors.white,
    },
    tipsBanner: {
        padding: spacing.md,
        marginBottom: spacing.lg,
        backgroundColor: colors.warning + '10',
        borderColor: colors.warning + '30',
    },
    tipsHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
        marginBottom: spacing.xs,
    },
    tipsTitle: {
        ...typography.bodySmall,
        fontWeight: '600',
        color: colors.inkPurple,
    },
    tipsText: {
        ...typography.caption,
        color: colors.mutedPurple,
    },
    loadingCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    loadingText: {
        ...typography.body,
        color: colors.dustyPurple,
        marginTop: spacing.md,
        textAlign: 'center',
    },
    errorCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    errorText: {
        ...typography.body,
        color: colors.error,
        marginTop: spacing.md,
        textAlign: 'center',
    },
    retryButton: {
        marginTop: spacing.md,
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.sm,
        backgroundColor: colors.neonPurple,
        borderRadius: borderRadius.md,
    },
    retryText: {
        ...typography.button,
    },
    emptyCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    emptyTitle: {
        ...typography.h3,
        marginTop: spacing.md,
    },
    emptyText: {
        ...typography.body,
        color: colors.dustyPurple,
        textAlign: 'center',
        marginTop: spacing.sm,
    },
    outletCard: {
        padding: spacing.lg,
        marginBottom: spacing.md,
    },
    outletHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: spacing.sm,
    },
    outletIcon: {
        width: 44,
        height: 44,
        borderRadius: 22,
        justifyContent: 'center',
        alignItems: 'center',
    },
    outletInfo: {
        flex: 1,
        marginLeft: spacing.md,
    },
    outletName: {
        ...typography.h3,
    },
    outletCategory: {
        ...typography.caption,
    },
    outletAddress: {
        ...typography.bodySmall,
        color: colors.mutedPurple,
        marginBottom: spacing.sm,
    },
    distanceBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        marginBottom: spacing.sm,
    },
    distanceText: {
        ...typography.caption,
    },
    nutrientMatch: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        backgroundColor: colors.success + '15',
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.sm,
        alignSelf: 'flex-start',
    },
    nutrientMatchText: {
        ...typography.caption,
        color: colors.success,
        fontWeight: '500',
    },
    
    // Food Suggestions Section
    foodSuggestionsSection: {
        marginBottom: spacing.lg,
    },
    sectionTitle: {
        ...typography.h3,
        marginBottom: spacing.xs,
    },
    sectionSubtitle: {
        ...typography.caption,
        color: colors.mutedPurple,
        marginBottom: spacing.md,
    },
    nutrientFoodCard: {
        padding: spacing.lg,
        marginBottom: spacing.md,
    },
    nutrientHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    nutrientIconContainer: {
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
    },
    nutrientTitleContainer: {
        marginLeft: spacing.md,
    },
    nutrientName: {
        ...typography.h3,
    },
    nutrientLabel: {
        ...typography.caption,
        color: colors.dustyPurple,
    },
    foodGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
        marginBottom: spacing.md,
    },
    foodItem: {
        width: '30%',
        backgroundColor: colors.lightOrchid + '30',
        borderRadius: borderRadius.md,
        padding: spacing.sm,
        alignItems: 'center',
    },
    foodEmoji: {
        fontSize: 28,
        marginBottom: spacing.xs,
    },
    foodName: {
        ...typography.bodySmall,
        fontWeight: '600',
        textAlign: 'center',
        marginBottom: 2,
    },
    foodBenefit: {
        ...typography.caption,
        fontSize: 10,
        textAlign: 'center',
        color: colors.dustyPurple,
    },
    nutrientTip: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: spacing.xs,
        backgroundColor: colors.lightOrchid + '20',
        padding: spacing.sm,
        borderRadius: borderRadius.sm,
    },
    nutrientTipText: {
        ...typography.caption,
        flex: 1,
        fontStyle: 'italic',
    },
    sectionDivider: {
        flexDirection: 'row',
        alignItems: 'center',
        marginVertical: spacing.lg,
    },
    dividerLine: {
        flex: 1,
        height: 1,
        backgroundColor: colors.lightOrchid,
    },
    dividerText: {
        ...typography.bodySmall,
        color: colors.dustyPurple,
        paddingHorizontal: spacing.md,
    },
    dietBadge: {
        backgroundColor: colors.success + '20',
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.full,
    },
    dietBadgeText: {
        ...typography.caption,
        color: colors.success,
        fontWeight: '600',
    },
    filteredNote: {
        ...typography.caption,
        color: colors.dustyPurple,
        fontStyle: 'italic',
        marginBottom: spacing.sm,
        textAlign: 'center',
    },
});
