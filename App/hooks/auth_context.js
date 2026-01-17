import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from 'react';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebaseConfig';

// 1. Create the Context
const UserContext = createContext(undefined);

// 2. Custom Hook with Error Handling
export const useUser = () => {
    const context = useContext(UserContext);
    if (context === undefined) {
        throw new Error('useUser must be used within a UserProvider');
    }
    return context;
};

// 3. Provider Component
export const UserProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    // Listen for Firebase Auth changes
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
            setIsLoading(false);
        });

        return () => unsubscribe();
    }, []);

    // Helper: Refresh user data (useful after email verification updates)
    const refreshUser = useCallback(async () => {
        if (auth.currentUser) {
            await auth.currentUser.reload();
            setUser(auth.currentUser); // Directly use the reloaded user object
        }
    }, []);

    // Helper: Get Access Token for API calls (Bearer Token)
    const getAccessToken = useCallback(async () => {
        if (user) {
            return await user.getIdToken();
        }
        return null;
    }, [user]);

    // Helper: Logout
    const logout = useCallback(async () => {
        try {
            await signOut(auth);
            // State updates handled by onAuthStateChanged automatically
        } catch (error) {
            console.error("Logout failed", error);
        }
    }, []);

    // 4. Derive State & Value
    // We use useMemo to prevent unnecessary re-renders in consumers
    const value = useMemo(() => {
        const isAuthenticated = !!user;
        const isEmailVerified = user ? user.emailVerified : false;
        const hasDisplayName = user ? !!user.displayName : false;

        return {
            // Base State
            user,
            isLoading,

            // Derived Flags
            isAuthenticated,
            isEmailVerified,
            hasDisplayName,

            // Actions
            refreshUser,
            getAccessToken,
            logout,

            // Route Guards (Centralized logic)
            canAccessTabs: isAuthenticated && hasDisplayName,
            canAccessOnboarding: isAuthenticated && !hasDisplayName,
            canAccessVerifyEmail: false, // Disabled - email verification not required
            shouldShowSignin: !isAuthenticated && !isLoading,
        };
    }, [user, isLoading, refreshUser, getAccessToken, logout]);

    return (
        <UserContext.Provider value={value}>
            {!isLoading && children}
        </UserContext.Provider>
    );
};