import { Stack } from 'expo-router';
import { UserProvider, useUser } from '../hooks/auth_context';
import Loader from '../components/Loader'
import { Text, View } from "react-native";

function RootLayoutContent() {
    const {
        isLoading,
        canAccessTabs,
        canAccessOnboarding,
        canAccessVerifyEmail,
        shouldShowSignin
    } = useUser();

    if (isLoading) {
        return <Loader />
    }

    return (
        <Stack screenOptions={{ headerShown: false }}>
            <Stack.Protected guard={canAccessTabs}>
                <Stack.Screen name="(tabs)" />
                <Stack.Screen name="chat" options={{ presentation: 'modal' }} />
                <Stack.Screen name="symptom-log" options={{ presentation: 'modal' }} />
                <Stack.Screen name="symptom-report" options={{ presentation: 'modal' }} />
                <Stack.Screen name="meal-log" options={{ presentation: 'modal' }} />
                <Stack.Screen name="water-log" options={{ presentation: 'modal' }} />
                <Stack.Screen name="hospitals" options={{ presentation: 'modal' }} />
            </Stack.Protected>
            <Stack.Protected guard={canAccessVerifyEmail}>
                <Stack.Screen name="VerifyEmail" />
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