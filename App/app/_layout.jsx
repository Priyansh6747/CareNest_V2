import { Stack } from 'expo-router';
import { UserProvider, useUser } from '../hooks/auth_context';
import Loader from '../components/Loader'
import {Text, View} from "react-native";

function RootLayoutContent() {
    const {
        isLoading,
        canAccessTabs,
        canAccessOnboarding,
        shouldShowSignin
    } = useUser();

    if (isLoading) {
        return <Loader/>
    }

    return (
        <Stack screenOptions={{ headerShown: false }}>
            <Stack.Protected guard={canAccessTabs}>
                <Stack.Screen name="(tabs)" />
            </Stack.Protected>
            <Stack.Protected guard={canAccessOnboarding}>
                <Stack.Screen name="Onboarding" />
            </Stack.Protected>
            <Stack.Protected guard={shouldShowSignin}>
                <Stack.Screen name="Signin" />
            </Stack.Protected>
        </Stack>
    );
}

export default function RootLayout() {
    return (
        <UserProvider>
            <RootLayoutContent />
        </UserProvider>
    );
}