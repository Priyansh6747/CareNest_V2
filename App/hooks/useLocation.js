import { useState } from 'react';
import * as Location from 'expo-location';

const useLocation = () => {
    const [location, setLocation] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const getLocation = async () => {
        setLoading(true);
        setError(null);

        try {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                throw new Error('Location permission denied');
            }

            const position = await Location.getCurrentPositionAsync({
                accuracy: Location.Accuracy.Balanced,
            });

            const coords = {
                lat: position.coords.latitude,
                lng: position.coords.longitude,
            };

            setLocation(coords);
            return coords;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    };

    const clearError = () => setError(null);

    return {
        location,
        loading,
        error,
        getLocation,
        clearError,
    };
};

export default useLocation;
