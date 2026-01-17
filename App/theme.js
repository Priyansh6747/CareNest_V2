/**
 * CareNest Theme
 * Lavender/Pink Glassmorphism Design System
 */

export const colors = {
    // Base / Background
    white: '#FEFDFE',
    softPinkLavender: '#F9E3FA',
    lightOrchid: '#F0CFF2',
    lightLavender: '#E0C5F0',

    // Brand / Accent
    neonPurple: '#AC04EC',
    mutedLavender: '#D5ADEA',
    dustyPurple: '#AA87AF',

    // Text
    inkPurple: '#1F0633',
    mutedPurple: '#684874',

    // Extra
    softBlue: '#76AAD6',

    // Functional
    success: '#4CAF50',
    warning: '#FF9800',
    error: '#F44336',
    transparent: 'transparent',
};

export const gradients = {
    background: [colors.softPinkLavender, colors.lightOrchid, colors.lightLavender],
    card: [colors.white, colors.lightOrchid],
    accent: [colors.neonPurple, colors.mutedLavender],
};

export const typography = {
    h1: {
        fontSize: 28,
        fontWeight: '700',
        color: colors.inkPurple,
    },
    h2: {
        fontSize: 22,
        fontWeight: '600',
        color: colors.inkPurple,
    },
    h3: {
        fontSize: 18,
        fontWeight: '600',
        color: colors.inkPurple,
    },
    body: {
        fontSize: 16,
        fontWeight: '400',
        color: colors.mutedPurple,
    },
    bodySmall: {
        fontSize: 14,
        fontWeight: '400',
        color: colors.mutedPurple,
    },
    caption: {
        fontSize: 12,
        fontWeight: '400',
        color: colors.dustyPurple,
    },
    button: {
        fontSize: 16,
        fontWeight: '600',
        color: colors.white,
    },
};

export const spacing = {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
};

export const borderRadius = {
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    full: 999,
};

export const shadows = {
    light: {
        shadowColor: colors.lightLavender,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.15,
        shadowRadius: 8,
        elevation: 3,
    },
    medium: {
        shadowColor: colors.dustyPurple,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 12,
        elevation: 6,
    },
    glow: {
        shadowColor: colors.neonPurple,
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.3,
        shadowRadius: 16,
        elevation: 8,
    },
};

export const glassmorphism = {
    card: {
        backgroundColor: 'rgba(254, 253, 254, 0.85)',
        borderRadius: borderRadius.lg,
        borderWidth: 1,
        borderColor: 'rgba(240, 207, 242, 0.5)',
        ...shadows.light,
    },
    floatingNav: {
        backgroundColor: 'rgba(254, 253, 254, 0.9)',
        borderRadius: borderRadius.xl,
        borderWidth: 1,
        borderColor: 'rgba(240, 207, 242, 0.6)',
        ...shadows.medium,
    },
};

export default {
    colors,
    gradients,
    typography,
    spacing,
    borderRadius,
    shadows,
    glassmorphism,
};
