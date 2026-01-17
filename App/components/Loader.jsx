import React from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, gradients } from '../theme';

export default function Loader() {
    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <View style={styles.loaderWrapper}>
                <ActivityIndicator size="large" color={colors.neonPurple} />
            </View>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loaderWrapper: {
        padding: 24,
        backgroundColor: 'rgba(254, 253, 254, 0.9)',
        borderRadius: 24,
    },
});