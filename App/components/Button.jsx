import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, typography, spacing, borderRadius, shadows } from '../theme';

export default function Button({
    title,
    onPress,
    variant = 'primary', // primary, secondary, outlined
    size = 'medium', // small, medium, large
    loading = false,
    disabled = false,
    icon,
    style,
}) {
    const isOutlined = variant === 'outlined';
    const isPrimary = variant === 'primary';

    const buttonStyles = [
        styles.base,
        styles[size],
        isOutlined && styles.outlined,
        !isPrimary && !isOutlined && styles.secondary,
        disabled && styles.disabled,
        style,
    ];

    const textStyles = [
        styles.text,
        styles[`${size}Text`],
        isOutlined && styles.outlinedText,
        !isPrimary && !isOutlined && styles.secondaryText,
    ];

    const content = (
        <>
            {loading ? (
                <ActivityIndicator
                    color={isOutlined ? colors.neonPurple : colors.white}
                    size="small"
                />
            ) : (
                <>
                    {icon}
                    <Text style={textStyles}>{title}</Text>
                </>
            )}
        </>
    );

    if (isPrimary && !disabled) {
        return (
            <TouchableOpacity
                onPress={onPress}
                disabled={disabled || loading}
                activeOpacity={0.8}
            >
                <LinearGradient
                    colors={[colors.neonPurple, colors.mutedLavender]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={[buttonStyles, styles.gradient]}
                >
                    {content}
                </LinearGradient>
            </TouchableOpacity>
        );
    }

    return (
        <TouchableOpacity
            style={buttonStyles}
            onPress={onPress}
            disabled={disabled || loading}
            activeOpacity={0.7}
        >
            {content}
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    base: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: spacing.sm,
        ...shadows.light,
    },
    gradient: {
        ...shadows.glow,
    },
    // Sizes
    small: {
        paddingVertical: spacing.sm,
        paddingHorizontal: spacing.md,
        borderRadius: borderRadius.sm,
    },
    medium: {
        paddingVertical: spacing.md,
        paddingHorizontal: spacing.lg,
        borderRadius: borderRadius.md,
    },
    large: {
        paddingVertical: spacing.lg,
        paddingHorizontal: spacing.xl,
        borderRadius: borderRadius.lg,
    },
    // Variants
    secondary: {
        backgroundColor: colors.mutedLavender,
    },
    outlined: {
        backgroundColor: 'transparent',
        borderWidth: 2,
        borderColor: colors.neonPurple,
    },
    disabled: {
        backgroundColor: colors.dustyPurple,
        opacity: 0.6,
    },
    // Text
    text: {
        ...typography.button,
    },
    smallText: {
        fontSize: 14,
    },
    mediumText: {
        fontSize: 16,
    },
    largeText: {
        fontSize: 18,
    },
    outlinedText: {
        color: colors.neonPurple,
    },
    secondaryText: {
        color: colors.inkPurple,
    },
});
