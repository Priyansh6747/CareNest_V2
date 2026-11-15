import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { UserProvider, useUser } from '../hooks/auth_context';
import Loader from '../components/Loader'
import useResponsive from '../hooks/useResponsive';

function RootLayoutContent() {
    const {
        isLoading,
        canAccessTabs,
        canAccessOnboarding,
        canAccessVerifyEmail,
        shouldShowSignin
    } = useUser();

    const { isDesktop } = useResponsive();

    if (isLoading) {
        return <Loader />
    }

    // On desktop browsers a centered card reads better than a full-screen page.
    const modalOptions = isDesktop
        ? { presentation: 'transparentModal', animation: 'fade', contentStyle: { backgroundColor: 'transparent' } }
        : { presentation: 'modal' };

    return (
        <Stack screenOptions={{ headerShown: false }}>
            <Stack.Protected guard={canAccessTabs}>
                <Stack.Screen name="(tabs)" />
                <Stack.Screen name="chat" options={modalOptions} />
                <Stack.Screen name="symptom-log" options={modalOptions} />
                <Stack.Screen name="symptom-report" options={modalOptions} />
                <Stack.Screen name="meal-log" options={modalOptions} />
                <Stack.Screen name="water-log" options={modalOptions} />
                <Stack.Screen name="hospitals" options={modalOptions} />
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
        <SafeAreaProvider>
            <UserProvider>
                <RootLayoutContent />
            </UserProvider>
        </SafeAreaProvider>
    );
}
