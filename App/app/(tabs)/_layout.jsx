import React from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';
import { colors, spacing, borderRadius, shadows } from '../../theme';
import useResponsive from '../../hooks/useResponsive';

export default function TabsLayout() {
    const { isDesktop, isTablet } = useResponsive();

    // Keep the floating pill compact on phones, but do not let it stretch
    // across a wide desktop viewport.
    const horizontalInset = isDesktop ? 0 : spacing.lg;
    const maxWidth = isDesktop ? 720 : isTablet ? 560 : undefined;

    return (
        <Tabs
            screenOptions={{
                headerShown: false,
                sceneStyle: styles.scene,
                tabBarStyle: [
                    styles.tabBar,
                    {
                        left: horizontalInset,
                        right: horizontalInset,
                        maxWidth,
                        alignSelf: 'center',
                        width: maxWidth ? '100%' : undefined,
                    },
                ],
                tabBarBackground: () => (
                    <BlurView intensity={80} tint="light" style={StyleSheet.absoluteFill} />
                ),
                tabBarActiveTintColor: colors.neonPurple,
                tabBarInactiveTintColor: colors.dustyPurple,
                tabBarShowLabel: true,
                tabBarLabelStyle: styles.tabBarLabel,
                tabBarItemStyle: styles.tabBarItem,
            }}
        >
            <Tabs.Screen
                name="index"
                options={{
                    title: 'Home',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="home" size={size} color={color} />
                    ),
                }}
            />
            <Tabs.Screen
                name="logs"
                options={{
                    title: 'Logs',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="list" size={size} color={color} />
                    ),
                }}
            />
            <Tabs.Screen
                name="profile"
                options={{
                    title: 'Profile',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="person" size={size} color={color} />
                    ),
                }}
            />
        </Tabs>
    );
}

const styles = StyleSheet.create({
    scene: {
        backgroundColor: colors.softPinkLavender,
    },
    tabBar: {
        position: 'absolute',
        bottom: spacing.lg,
        height: 70,
        borderRadius: borderRadius.xl,
        backgroundColor: 'rgba(254, 253, 254, 0.9)',
        borderTopWidth: 0,
        borderWidth: 1,
        borderColor: 'rgba(240, 207, 242, 0.6)',
        ...shadows.medium,
        paddingBottom: 0,
        ...(Platform.OS === 'web' ? { overflow: 'hidden' } : null),
    },
    tabBarItem: {
        paddingVertical: spacing.sm,
    },
    tabBarLabel: {
        fontSize: 12,
        fontWeight: '600',
        marginBottom: spacing.xs,
    },
});
