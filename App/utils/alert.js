import { Alert, Platform } from 'react-native';

/**
 * Cross-platform alert.
 *
 * `Alert.alert` is a no-op on react-native-web, so web falls back to the
 * browser dialogs. Buttons with an `onPress` are honoured on web via confirm().
 */
export function showAlert(title, message, buttons) {
    if (Platform.OS !== 'web') {
        Alert.alert(title, message, buttons);
        return;
    }

    const text = [title, message].filter(Boolean).join('\n\n');

    if (!buttons || buttons.length === 0) {
        window.alert(text);
        return;
    }

    const cancelButton = buttons.find((b) => b.style === 'cancel');
    const confirmButton = buttons.find((b) => b.style !== 'cancel');

    if (!cancelButton) {
        window.alert(text);
        confirmButton?.onPress?.();
        return;
    }

    if (window.confirm(text)) {
        confirmButton?.onPress?.();
    } else {
        cancelButton.onPress?.();
    }
}

export default showAlert;
