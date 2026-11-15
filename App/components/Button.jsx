import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator, View } from 'react-native';
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
    textStyle,
    fullWidth = true,
}) {
    const isOutlined = variant === 'outlined';
    const isPrimary = variant === 'primary';
    const isDisabled = disabled || loading;

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
        textStyle,
    ];

    const content = loading ? (
        <ActivityIndicator
            color={isOutlined ? colors.neonPurple : colors.white}
            size="small"
        />
    ) : (
        <>
            {icon}
            <Text style={textStyles} numberOfLines={1}>{title}</Text>
        </>
    );

    // The touchable owns layout (width/flex) so callers can size it reliably;
    // the visual surface is drawn by the inner gradient/view.
    return (
        <TouchableOpacity
            style={[styles.touchable, fullWidth && styles.fullWidth, style]}
            onPress={onPress}
            disabled={isDisabled}
            activeOpacity={0.8}
        >
            {isPrimary && !isDisabled ? (
                <LinearGradient
                    colors={[colors.neonPurple, colors.mutedLavender]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={[styles.surface, styles[size], styles.gradient]}
                >
                    {content}
                </LinearGradient>
            ) : (
                <View
                    style={[
                        styles.surface,
                        styles[size],
                        isOutlined && styles.outlined,
                        !isPrimary && !isOutlined && styles.secondary,
                        disabled && styles.disabled,
                    ]}
                >
                    {content}
                </View>
            )}
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    touchable: {
        alignSelf: 'flex-start',
    },
    fullWidth: {
        alignSelf: 'stretch',
    },
    surface: {
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
