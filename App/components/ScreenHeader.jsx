import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, typography, spacing } from '../theme';

/**
 * Shared header for the modal/detail screens.
 *
 * Keeps the back button and centred title identical everywhere, and on web it
 * renders a labelled "Back" control that is easier to hit with a mouse.
 */
export default function ScreenHeader({ title, onBack, isWeb = false }) {
    const router = useRouter();

    const handleBack = onBack || (() => {
        if (router.canGoBack()) {
            router.back();
        } else {
            router.replace('/(tabs)');
        }
    });

    return (
        <View style={styles.header}>
            <TouchableOpacity
                onPress={handleBack}
                style={[styles.backButton, isWeb && styles.backButtonWeb]}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
                <Ionicons name="arrow-back" size={24} color={colors.inkPurple} />
                {isWeb && <Text style={styles.backLabel}>Back</Text>}
            </TouchableOpacity>
            <Text style={styles.title} numberOfLines={1}>{title}</Text>
            <View style={styles.spacer} />
        </View>
    );
}

const styles = StyleSheet.create({
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: spacing.lg,
        gap: spacing.sm,
    },
    backButton: {
        padding: spacing.sm,
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        minWidth: 40,
    },
    backButtonWeb: {
        minWidth: 90,
    },
    backLabel: {
        ...typography.body,
        fontWeight: '600',
        color: colors.inkPurple,
    },
    title: {
        ...typography.h2,
        flex: 1,
        textAlign: 'center',
    },
    spacer: {
        minWidth: 40,
    },
});
