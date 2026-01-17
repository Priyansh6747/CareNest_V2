import React, { useState, useRef, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TextInput,
    TouchableOpacity,
    SafeAreaView,
    StatusBar,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useUser } from '../hooks/auth_context';
import Card from '../components/Card';
import { colors, gradients, typography, spacing, borderRadius, shadows, glassmorphism } from '../theme';
import { ChatAPI } from '../services/apiService';

export default function Chat() {
    const router = useRouter();
    const { user } = useUser();
    const scrollViewRef = useRef(null);

    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);

    const userId = user?.uid;

    useEffect(() => {
        if (userId) {
            loadHistory();
        }
    }, [userId]);

    const loadHistory = async () => {
        try {
            const history = await ChatAPI.getHistory(userId, 20);
            if (history?.messages) {
                setMessages(history.messages.map(m => ({
                    id: m.id,
                    text: m.content,
                    isUser: m.role === 'user',
                })).reverse());
            }
        } catch (err) {
            console.log('Failed to load chat history');
        }
    };

    const sendMessage = async () => {
        if (!inputText.trim() || loading) return;

        const userMessage = { id: Date.now().toString(), text: inputText, isUser: true };
        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setLoading(true);

        try {
            const response = await ChatAPI.sendMessage(userId, {
                message: inputText,
                provider: 'groq',
            });

            const aiMessage = {
                id: (Date.now() + 1).toString(),
                text: response.message,
                isUser: false,
                sources: response.sources,
            };
            setMessages(prev => [...prev, aiMessage]);
        } catch (err) {
            const errorMessage = {
                id: (Date.now() + 1).toString(),
                text: 'Sorry, I couldn\'t process your message. Please try again.',
                isUser: false,
                isError: true,
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const scrollToBottom = () => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    return (
        <LinearGradient colors={gradients.background} style={styles.container}>
            <StatusBar barStyle="dark-content" />
            <SafeAreaView style={styles.safeArea}>
                <KeyboardAvoidingView
                    style={styles.keyboardView}
                    behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                >
                    {/* Header */}
                    <View style={styles.header}>
                        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                            <Ionicons name="arrow-back" size={24} color={colors.inkPurple} />
                        </TouchableOpacity>
                        <Text style={styles.title}>Health Assistant</Text>
                        <View style={{ width: 40 }} />
                    </View>

                    {/* Messages */}
                    <ScrollView
                        ref={scrollViewRef}
                        style={styles.messagesContainer}
                        contentContainerStyle={styles.messagesContent}
                        showsVerticalScrollIndicator={false}
                    >
                        {messages.length === 0 && (
                            <View style={styles.emptyState}>
                                <Ionicons name="chatbubbles-outline" size={48} color={colors.dustyPurple} />
                                <Text style={styles.emptyText}>
                                    Ask me anything about pregnancy, nutrition, or health!
                                </Text>
                            </View>
                        )}

                        {messages.map((message) => (
                            <View
                                key={message.id}
                                style={[
                                    styles.messageBubble,
                                    message.isUser ? styles.userBubble : styles.aiBubble,
                                    message.isError && styles.errorBubble,
                                ]}
                            >
                                <Text style={[
                                    styles.messageText,
                                    message.isUser && styles.userMessageText,
                                ]}>
                                    {message.text}
                                </Text>
                                {message.sources && message.sources.length > 0 && (
                                    <Text style={styles.sourcesText}>
                                        📚 {message.sources.length} source(s)
                                    </Text>
                                )}
                            </View>
                        ))}

                        {loading && (
                            <View style={[styles.messageBubble, styles.aiBubble]}>
                                <Text style={styles.messageText}>Thinking...</Text>
                            </View>
                        )}
                    </ScrollView>

                    {/* Input */}
                    <View style={styles.inputContainer}>
                        <TextInput
                            style={styles.input}
                            value={inputText}
                            onChangeText={setInputText}
                            placeholder="Type your message..."
                            placeholderTextColor={colors.dustyPurple}
                            multiline
                            maxLength={500}
                        />
                        <TouchableOpacity
                            style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
                            onPress={sendMessage}
                            disabled={!inputText.trim() || loading}
                        >
                            <LinearGradient
                                colors={inputText.trim() ? [colors.neonPurple, colors.mutedLavender] : [colors.dustyPurple, colors.dustyPurple]}
                                style={styles.sendButtonGradient}
                            >
                                <Ionicons name="send" size={20} color={colors.white} />
                            </LinearGradient>
                        </TouchableOpacity>
                    </View>
                </KeyboardAvoidingView>
            </SafeAreaView>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    safeArea: {
        flex: 1,
    },
    keyboardView: {
        flex: 1,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: spacing.md,
        paddingTop: spacing.lg,
    },
    backButton: {
        padding: spacing.sm,
    },
    title: {
        ...typography.h2,
    },
    messagesContainer: {
        flex: 1,
    },
    messagesContent: {
        padding: spacing.md,
        paddingBottom: spacing.lg,
    },
    emptyState: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: spacing.xxl * 2,
    },
    emptyText: {
        ...typography.body,
        color: colors.dustyPurple,
        textAlign: 'center',
        marginTop: spacing.md,
        paddingHorizontal: spacing.xl,
    },
    messageBubble: {
        maxWidth: '80%',
        padding: spacing.md,
        borderRadius: borderRadius.lg,
        marginBottom: spacing.sm,
    },
    userBubble: {
        alignSelf: 'flex-end',
        backgroundColor: colors.neonPurple,
    },
    aiBubble: {
        alignSelf: 'flex-start',
        ...glassmorphism.card,
    },
    errorBubble: {
        borderColor: colors.error,
    },
    messageText: {
        ...typography.body,
        color: colors.inkPurple,
    },
    userMessageText: {
        color: colors.white,
    },
    sourcesText: {
        ...typography.caption,
        marginTop: spacing.xs,
        color: colors.dustyPurple,
    },
    inputContainer: {
        flexDirection: 'row',
        padding: spacing.md,
        gap: spacing.sm,
        alignItems: 'flex-end',
    },
    input: {
        flex: 1,
        ...glassmorphism.card,
        padding: spacing.md,
        ...typography.body,
        color: colors.inkPurple,
        maxHeight: 100,
    },
    sendButton: {
        ...shadows.light,
    },
    sendButtonDisabled: {
        opacity: 0.5,
    },
    sendButtonGradient: {
        width: 48,
        height: 48,
        borderRadius: 24,
        justifyContent: 'center',
        alignItems: 'center',
    },
});
