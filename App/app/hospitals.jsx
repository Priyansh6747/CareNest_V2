import React, { useState, useEffect, useCallback } from 'react';
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
    ActivityIndicator,
    RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { Dropdown } from 'react-native-element-dropdown';
import { useRouter } from 'expo-router';

import useLocation from '../hooks/useLocation';
import Card from '../components/Card';
import Button from '../components/Button';
import { colors, gradients, typography, spacing, borderRadius, shadows, glassmorphism } from '../theme';
import { HospitalAPI } from '../services/apiService';

const HOSPITAL_COUNT_OPTIONS = [
    { label: '5 Hospitals', value: 5 },
    { label: '10 Hospitals', value: 10 },
    { label: '15 Hospitals', value: 15 },
    { label: '20 Hospitals', value: 20 },
];

const RADIUS_OPTIONS = [
    { label: '5 km', value: 5 },
    { label: '10 km', value: 10 },
    { label: '15 km', value: 15 },
    { label: '20 km', value: 20 },
    { label: '25 km', value: 25 },
];

export default function Hospitals() {
    const router = useRouter();
    const { location, loading: locationLoading, error: locationError, getLocation, clearError } = useLocation();

    const [hospitals, setHospitals] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [refreshing, setRefreshing] = useState(false);

    // Filter states
    const [hospitalCount, setHospitalCount] = useState(5);
    const [radius, setRadius] = useState(10);

    const fetchHospitals = useCallback(async (coords = location) => {
        if (!coords) {
            const newCoords = await getLocation();
            if (!newCoords) return;
            coords = newCoords;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await HospitalAPI.findNearbyHospitals({
                lat: coords.lat,
                lng: coords.lng,
                radius: radius * 1000, // Convert km to meters
                limit: hospitalCount,
            });
            setHospitals(response.hospitals || []);
        } catch (err) {
            setError('Failed to load hospitals. Please try again.');
            console.log('Hospital fetch error:', err.message);
        } finally {
            setLoading(false);
        }
    }, [location, hospitalCount, radius, getLocation]);

    // Initial fetch
    useEffect(() => {
        fetchHospitals();
    }, []);

    // Refetch when filters change
    useEffect(() => {
        if (location) {
            fetchHospitals(location);
        }
    }, [hospitalCount, radius]);

    const onRefresh = async () => {
        setRefreshing(true);
        await fetchHospitals();
        setRefreshing(false);
    };

    const handleCall = (phone) => {
        if (phone) {
            Linking.openURL(`tel:${phone}`);
        }
    };

    const handleDirections = (hospital) => {
        const { lat, lng } = hospital.location || {};
        if (lat && lng) {
            const url = Platform.select({
                ios: `maps:?daddr=${lat},${lng}`,
                android: `geo:${lat},${lng}?q=${lat},${lng}(${encodeURIComponent(hospital.name)})`,
            });
            Linking.openURL(url);
        }
    };

    const isLoading = locationLoading || loading;
    const hasError = locationError || error;

    // Loading State
    if (isLoading && hospitals.length === 0) {
        return (
            <LinearGradient colors={gradients.background} style={styles.container}>
                <StatusBar barStyle="dark-content" />
                <SafeAreaView style={styles.centered}>
                    <View style={styles.loadingCard}>
                        <ActivityIndicator size="large" color={colors.neonPurple} />
                        <Text style={styles.loadingText}>
                            {locationLoading ? 'Getting your location...' : 'Finding hospitals...'}
                        </Text>
                    </View>
                </SafeAreaView>
            </LinearGradient>
        );
    }

    // Error State
    if (hasError && hospitals.length === 0) {
        return (
            <LinearGradient colors={gradients.background} style={styles.container}>
                <StatusBar barStyle="dark-content" />
                <SafeAreaView style={styles.safeArea}>
                    <View style={styles.header}>
                        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                            <Ionicons name="arrow-back" size={24} color={colors.inkPurple} />
                        </TouchableOpacity>
                        <Text style={styles.title}>Nearby Hospitals</Text>
                        <View style={{ width: 40 }} />
                    </View>
                    <View style={styles.centered}>
                        <Card style={styles.errorCard}>
                            <Ionicons name="warning-outline" size={48} color={colors.error} />
                            <Text style={styles.errorTitle}>Something went wrong</Text>
                            <Text style={styles.errorText}>{locationError || error}</Text>
                            <Button
                                title="Try Again"
                                onPress={() => {
                                    clearError();
                                    setError(null);
                                    fetchHospitals();
                                }}
                                style={{ marginTop: spacing.lg }}
                            />
                        </Card>
                    </View>
                </SafeAreaView>
            </LinearGradient>
        );
    }

    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <SafeAreaView style={styles.safeArea}>
                {/* Header */}
                <View style={styles.header}>
                    <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                        <Ionicons name="arrow-back" size={24} color={colors.inkPurple} />
                    </TouchableOpacity>
                    <Text style={styles.title}>Nearby Hospitals</Text>
                    <View style={{ width: 40 }} />
                </View>

                {/* Filters */}
                <View style={styles.filtersContainer}>
                    <View style={styles.filterRow}>
                        <View style={styles.dropdownWrapper}>
                            <Text style={styles.dropdownLabel}>Count</Text>
                            <Dropdown
                                style={styles.dropdown}
                                placeholderStyle={styles.dropdownText}
                                selectedTextStyle={styles.dropdownText}
                                itemTextStyle={styles.dropdownItemText}
                                containerStyle={styles.dropdownContainer}
                                activeColor={colors.lightOrchid}
                                data={HOSPITAL_COUNT_OPTIONS}
                                maxHeight={200}
                                labelField="label"
                                valueField="value"
                                value={hospitalCount}
                                onChange={(item) => setHospitalCount(item.value)}
                            />
                        </View>

                        <View style={styles.dropdownWrapper}>
                            <Text style={styles.dropdownLabel}>Radius</Text>
                            <Dropdown
                                style={styles.dropdown}
                                placeholderStyle={styles.dropdownText}
                                selectedTextStyle={styles.dropdownText}
                                itemTextStyle={styles.dropdownItemText}
                                containerStyle={styles.dropdownContainer}
                                activeColor={colors.lightOrchid}
                                data={RADIUS_OPTIONS}
                                maxHeight={200}
                                labelField="label"
                                valueField="value"
                                value={radius}
                                onChange={(item) => setRadius(item.value)}
                            />
                        </View>
                    </View>
                </View>

                {/* Hospital List */}
                <ScrollView
                    style={styles.scrollView}
                    contentContainerStyle={styles.scrollContent}
                    showsVerticalScrollIndicator={false}
                    refreshControl={
                        <RefreshControl
                            refreshing={refreshing}
                            onRefresh={onRefresh}
                            tintColor={colors.neonPurple}
                        />
                    }
                >
                    {hospitals.length === 0 ? (
                        <Card style={styles.emptyCard}>
                            <Ionicons name="medical-outline" size={48} color={colors.dustyPurple} />
                            <Text style={styles.emptyText}>No hospitals found in this area</Text>
                            <Text style={styles.emptySubtext}>Try increasing the search radius</Text>
                        </Card>
                    ) : (
                        hospitals.map((hospital, index) => (
                            <Card key={`hospital-${index}`} style={styles.hospitalCard}>
                                <View style={styles.hospitalHeader}>
                                    <View style={styles.hospitalIcon}>
                                        <Ionicons name="medical" size={24} color={colors.neonPurple} />
                                    </View>
                                    <View style={styles.hospitalInfo}>
                                        <Text style={styles.hospitalName} numberOfLines={2}>
                                            {hospital.name}
                                        </Text>
                                        {hospital.location && (
                                            <View style={styles.coordsRow}>
                                                <Ionicons name="location" size={12} color={colors.dustyPurple} />
                                                <Text style={styles.coords}>
                                                    {hospital.location.lat?.toFixed(4)}, {hospital.location.lng?.toFixed(4)}
                                                </Text>
                                            </View>
                                        )}
                                    </View>
                                </View>

                                {hospital.address && (
                                    <Text style={styles.address} numberOfLines={2}>
                                        {hospital.address}
                                    </Text>
                                )}

                                <View style={styles.actions}>
                                    <TouchableOpacity
                                        style={styles.actionButton}
                                        onPress={() => handleDirections(hospital)}
                                    >
                                        <Ionicons name="navigate" size={18} color={colors.neonPurple} />
                                        <Text style={styles.actionText}>Directions</Text>
                                    </TouchableOpacity>

                                    {hospital.phone && (
                                        <TouchableOpacity
                                            style={styles.actionButton}
                                            onPress={() => handleCall(hospital.phone)}
                                        >
                                            <Ionicons name="call" size={18} color={colors.softBlue} />
                                            <Text style={[styles.actionText, { color: colors.softBlue }]}>Call</Text>
                                        </TouchableOpacity>
                                    )}
                                </View>
                            </Card>
                        ))
                    )}
                </ScrollView>

                {/* Refresh Button */}
                <View style={styles.refreshButtonContainer}>
                    <TouchableOpacity onPress={onRefresh} disabled={isLoading}>
                        <LinearGradient
                            colors={[colors.neonPurple, colors.mutedLavender]}
                            start={{ x: 0, y: 0 }}
                            end={{ x: 1, y: 0 }}
                            style={styles.refreshButton}
                        >
                            {isLoading ? (
                                <ActivityIndicator size="small" color={colors.white} />
                            ) : (
                                <>
                                    <Ionicons name="refresh" size={20} color={colors.white} />
                                    <Text style={styles.refreshButtonText}>Refresh</Text>
                                </>
                            )}
                        </LinearGradient>
                    </TouchableOpacity>
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
    centered: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: spacing.lg,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.md,
    },
    backButton: {
        padding: spacing.sm,
    },
    title: {
        ...typography.h2,
    },
    // Loading
    loadingCard: {
        ...glassmorphism.card,
        padding: spacing.xl,
        alignItems: 'center',
    },
    loadingText: {
        ...typography.body,
        color: colors.mutedPurple,
        marginTop: spacing.md,
    },
    // Error
    errorCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    errorTitle: {
        ...typography.h3,
        marginTop: spacing.md,
        marginBottom: spacing.sm,
    },
    errorText: {
        ...typography.body,
        color: colors.mutedPurple,
        textAlign: 'center',
    },
    // Filters
    filtersContainer: {
        paddingHorizontal: spacing.lg,
        marginBottom: spacing.md,
    },
    filterRow: {
        flexDirection: 'row',
        gap: spacing.md,
    },
    dropdownWrapper: {
        flex: 1,
    },
    dropdownLabel: {
        ...typography.bodySmall,
        fontWeight: '600',
        color: colors.inkPurple,
        marginBottom: spacing.xs,
    },
    dropdown: {
        ...glassmorphism.card,
        height: 48,
        paddingHorizontal: spacing.md,
    },
    dropdownText: {
        ...typography.body,
        color: colors.inkPurple,
    },
    dropdownItemText: {
        ...typography.body,
        color: colors.inkPurple,
    },
    dropdownContainer: {
        backgroundColor: colors.white,
        borderRadius: borderRadius.md,
        borderWidth: 1,
        borderColor: colors.lightOrchid,
        ...shadows.medium,
    },
    // List
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: spacing.lg,
        paddingTop: 0,
        paddingBottom: spacing.xxl,
    },
    emptyCard: {
        padding: spacing.xl,
        alignItems: 'center',
    },
    emptyText: {
        ...typography.h3,
        marginTop: spacing.md,
    },
    emptySubtext: {
        ...typography.bodySmall,
        color: colors.dustyPurple,
        marginTop: spacing.xs,
    },
    // Hospital Card
    hospitalCard: {
        marginBottom: spacing.md,
        padding: spacing.lg,
    },
    hospitalHeader: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: spacing.md,
        marginBottom: spacing.sm,
    },
    hospitalIcon: {
        width: 48,
        height: 48,
        borderRadius: 24,
        backgroundColor: colors.neonPurple + '20',
        justifyContent: 'center',
        alignItems: 'center',
    },
    hospitalInfo: {
        flex: 1,
    },
    hospitalName: {
        ...typography.h3,
        marginBottom: spacing.xs,
    },
    coordsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
    },
    coords: {
        ...typography.caption,
        color: colors.dustyPurple,
    },
    address: {
        ...typography.body,
        color: colors.mutedPurple,
        marginBottom: spacing.md,
    },
    actions: {
        flexDirection: 'row',
        gap: spacing.lg,
        borderTopWidth: 1,
        borderTopColor: colors.lightOrchid,
        paddingTop: spacing.md,
    },
    actionButton: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
    },
    actionText: {
        ...typography.body,
        fontWeight: '600',
        color: colors.neonPurple,
    },
    // Refresh Button
    refreshButtonContainer: {
        alignItems: 'center',
        paddingVertical: spacing.md,
        paddingBottom: spacing.lg,
    },
    refreshButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: spacing.sm,
        paddingVertical: spacing.md,
        paddingHorizontal: spacing.xl,
        borderRadius: borderRadius.lg,
        ...shadows.glow,
    },
    refreshButtonText: {
        ...typography.button,
    },
});
