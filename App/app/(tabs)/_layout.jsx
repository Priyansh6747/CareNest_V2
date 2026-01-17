import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';
import { colors, spacing, borderRadius, shadows } from '../../theme';

export default function TabsLayout() {
    return (
        <Tabs
            screenOptions={{
                headerShown: false,
                tabBarStyle: styles.tabBar,
                tabBarBackground: () => (
                    <BlurView intensity={80} tint="light" style={StyleSheet.absoluteFill} />
                ),
                tabBarActiveTintColor: colors.neonPurple,
                tabBarInactiveTintColor: colors.dustyPurple,
                tabBarShowLabel: true,
                tabBarLabelStyle: styles.tabBarLabel,
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
    tabBar: {
        position: 'absolute',
        bottom: spacing.lg,
        left: spacing.lg,
        right: spacing.lg,
        height: 70,
        borderRadius: borderRadius.xl,
        backgroundColor: 'rgba(254, 253, 254, 0.9)',
        borderTopWidth: 0,
        borderWidth: 1,
        borderColor: 'rgba(240, 207, 242, 0.6)',
        ...shadows.medium,
        paddingBottom: 0,
    },
    tabBarLabel: {
        fontSize: 12,
        fontWeight: '600',
        marginBottom: spacing.sm,
    },
});
