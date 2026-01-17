import React from 'react';
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

import { useUser } from '../../hooks/auth_context';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { colors, gradients, typography, spacing, borderRadius, shadows, glassmorphism } from '../../theme';

export default function Profile() {
    const { user, logout, isEmailVerified } = useUser();

    const displayName = user?.displayName || 'User';
    const email = user?.email || '';

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
                <ScrollView
                    style={styles.scrollView}
                    contentContainerStyle={styles.scrollContent}
                    showsVerticalScrollIndicator={false}
                >
                    {/* Header */}
                    <View style={styles.header}>
                        <Text style={styles.title}>Profile</Text>
                    </View>

                    {/* Profile Card */}
                    <Card style={styles.profileCard}>
                        <View style={styles.avatarContainer}>
                            <LinearGradient
                                colors={[colors.neonPurple, colors.mutedLavender]}
                                style={styles.avatar}
                            >
                                <Text style={styles.avatarText}>
                                    {displayName.charAt(0).toUpperCase()}
                                </Text>
                            </LinearGradient>
                        </View>
                        <Text style={styles.name}>{displayName}</Text>
                        <Text style={styles.email}>{email}</Text>
                        {isEmailVerified && (
                            <View style={styles.verifiedBadge}>
                                <Ionicons name="checkmark-circle" size={16} color={colors.success} />
                                <Text style={styles.verifiedText}>Verified</Text>
                            </View>
                        )}
                    </Card>

                    {/* Settings Section */}
                    <Text style={styles.sectionTitle}>Settings</Text>

                    <Card style={styles.settingsCard}>
                        <TouchableOpacity style={styles.settingsItem}>
                            <Ionicons name="person-outline" size={24} color={colors.neonPurple} />
                            <Text style={styles.settingsText}>Edit Profile</Text>
                            <Ionicons name="chevron-forward" size={20} color={colors.dustyPurple} />
                        </TouchableOpacity>

                        <View style={styles.divider} />

                        <TouchableOpacity style={styles.settingsItem}>
                            <Ionicons name="notifications-outline" size={24} color={colors.neonPurple} />
                            <Text style={styles.settingsText}>Notifications</Text>
                            <Ionicons name="chevron-forward" size={20} color={colors.dustyPurple} />
                        </TouchableOpacity>

                        <View style={styles.divider} />

                        <TouchableOpacity style={styles.settingsItem}>
                            <Ionicons name="shield-checkmark-outline" size={24} color={colors.neonPurple} />
                            <Text style={styles.settingsText}>Privacy</Text>
                            <Ionicons name="chevron-forward" size={20} color={colors.dustyPurple} />
                        </TouchableOpacity>

                        <View style={styles.divider} />

                        <TouchableOpacity style={styles.settingsItem}>
                            <Ionicons name="help-circle-outline" size={24} color={colors.neonPurple} />
                            <Text style={styles.settingsText}>Help & Support</Text>
                            <Ionicons name="chevron-forward" size={20} color={colors.dustyPurple} />
                        </TouchableOpacity>
                    </Card>

                    {/* Logout Button */}
                    <View style={styles.logoutSection}>
                        <Button
                            title="Logout"
                            onPress={handleLogout}
                            variant="outlined"
                            icon={<Ionicons name="log-out-outline" size={20} color={colors.neonPurple} />}
                        />
                    </View>

                    {/* App Info */}
                    <Text style={styles.appInfo}>CareNest v1.0.0</Text>

                    {/* Spacer for tab bar */}
                    <View style={{ height: 100 }} />
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
        marginBottom: spacing.lg,
        marginTop: spacing.md,
    },
    title: {
        ...typography.h1,
    },
    profileCard: {
        alignItems: 'center',
        padding: spacing.xl,
        marginBottom: spacing.xl,
    },
    avatarContainer: {
        marginBottom: spacing.md,
    },
    avatar: {
        width: 80,
        height: 80,
        borderRadius: 40,
        justifyContent: 'center',
        alignItems: 'center',
        ...shadows.glow,
    },
    avatarText: {
        ...typography.h1,
        color: colors.white,
        fontSize: 32,
    },
    name: {
        ...typography.h2,
        marginBottom: spacing.xs,
    },
    email: {
        ...typography.body,
        color: colors.mutedPurple,
    },
    verifiedBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        marginTop: spacing.sm,
        backgroundColor: colors.success + '20',
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.full,
    },
    verifiedText: {
        ...typography.caption,
        color: colors.success,
        fontWeight: '600',
    },
    sectionTitle: {
        ...typography.h3,
        marginBottom: spacing.md,
    },
    settingsCard: {
        padding: 0,
        overflow: 'hidden',
    },
    settingsItem: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: spacing.md,
        gap: spacing.md,
    },
    settingsText: {
        ...typography.body,
        flex: 1,
        color: colors.inkPurple,
    },
    divider: {
        height: 1,
        backgroundColor: colors.lightOrchid,
        marginHorizontal: spacing.md,
    },
    logoutSection: {
        marginTop: spacing.xl,
    },
    appInfo: {
        ...typography.caption,
        textAlign: 'center',
        marginTop: spacing.xl,
    },
});
