import React from 'react';
import { View, StyleSheet } from 'react-native';
import useResponsive from '../hooks/useResponsive';

/**
 * Centers screen content in a readable column on tablets and desktop browsers
 * while keeping full-bleed layout on phones.
 */
export default function ScreenContainer({ children, style, maxWidth }) {
    const { maxContentWidth, pagePadding } = useResponsive();
    const limit = maxWidth ?? maxContentWidth;

    return (
        <View style={[styles.outer, { paddingHorizontal: pagePadding }, style]}>
            <View style={[styles.inner, limit ? { maxWidth: limit, width: '100%' } : null]}>
                {children}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    outer: {
        width: '100%',
        alignItems: 'center',
    },
    inner: {
        flex: 1,
        width: '100%',
    },
});
