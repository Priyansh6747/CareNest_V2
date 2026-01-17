import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { colors, typography, spacing, glassmorphism } from '../theme';

export default function Card({
    children,
    title,
    subtitle,
    onPress,
    style,
    icon,
}) {
    const Wrapper = onPress ? TouchableOpacity : View;

    return (
        <Wrapper
            style={[styles.card, style]}
            onPress={onPress}
            activeOpacity={0.7}
        >
            {icon && <View style={styles.iconWrapper}>{icon}</View>}
            {title && <Text style={styles.title}>{title}</Text>}
            {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
            {children}
        </Wrapper>
    );
}

const styles = StyleSheet.create({
    card: {
        ...glassmorphism.card,
        padding: spacing.md,
    },
    iconWrapper: {
        alignSelf: 'center',
        marginBottom: spacing.sm,
    },
    title: {
        ...typography.h3,
        textAlign: 'center',
        marginBottom: spacing.xs,
    },
    subtitle: {
        ...typography.bodySmall,
        textAlign: 'center',
    },
});
