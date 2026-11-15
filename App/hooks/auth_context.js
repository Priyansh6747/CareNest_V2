import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from 'react';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebaseConfig';
import { UserAPI } from '../services/apiService';

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
    // Bumped whenever we reload the user so consumers re-read fresh fields.
    const [authVersion, setAuthVersion] = useState(0);

    // Listen for Firebase Auth changes
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
            setIsLoading(false);

            // Self-heal accounts created before firebase_uid was stored: without
            // the link, profile endpoints (allergies etc.) cannot resolve the
            // Firebase UID to a maternal profile. Safe to call repeatedly.
            if (currentUser?.email) {
                UserAPI.linkAccount(currentUser.uid, currentUser.email).catch(() => {
                    // Non-fatal: the account may not have a backend user doc yet.
                });
            }
        });

        return () => unsubscribe();
    }, []);

    // Helper: Refresh user data (useful after email verification/onboarding updates)
    const refreshUser = useCallback(async () => {
        if (!auth.currentUser) return;

        await auth.currentUser.reload();

        // `reload()` mutates the existing User instance in place. Re-setting the
        // same reference makes React bail out, so the route guards never
        // re-evaluate and the app appears stuck. A version bump forces it.
        setAuthVersion((v) => v + 1);
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
        // authVersion is included so a reload() re-derives the guards even
        // though the underlying User instance is mutated in place.
    }, [user, isLoading, authVersion, refreshUser, getAccessToken, logout]);

    return (
        <UserContext.Provider value={value}>
            {!isLoading && children}
        </UserContext.Provider>
    );
};