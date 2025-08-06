// frontend/src/crypto.ts
import { box, randomBytes, secretbox, sign } from 'tweetnacl';
import {
  decodeBase64,
  encodeBase64,
  decodeUTF8,
  encodeUTF8,
} from 'tweetnacl-util';

const newNonce = () => randomBytes(secretbox.nonceLength);

/**
 * Generates a new signing key pair.
 * @returns {nacl.SignKeyPair} A key pair with `publicKey` and `secretKey`.
 */
export const generateKeyPair = () => sign.keyPair();

/**
 * Encrypts a private key using a passphrase.
 * @param {Uint8Array} secretKey The private key to encrypt.
 * @param {string} passphrase The user's passphrase.
 * @returns {string} A base64 encoded string of the encrypted key.
 */
export const encryptPrivateKey = (secretKey: Uint8Array, passphrase: string): string => {
  const nonce = newNonce();
  const key = decodeUTF8(passphrase.padEnd(32, ' ')).slice(0, 32); // Ensure key is 32 bytes
  const encrypted = secretbox(secretKey, nonce, key);

  const fullMessage = new Uint8Array(nonce.length + encrypted.length);
  fullMessage.set(nonce);
  fullMessage.set(encrypted, nonce.length);

  return encodeBase64(fullMessage);
};

/**
 * Decrypts a private key using a passphrase.
 * @param {string} encryptedKeyB64 The base64 encoded encrypted key.
 * @param {string} passphrase The user's passphrase.
 * @returns {Uint8Array | null} The decrypted private key or null if decryption fails.
 */
export const decryptPrivateKey = (encryptedKeyB64: string, passphrase: string): Uint8Array | null => {
  const key = decodeUTF8(passphrase.padEnd(32, ' ')).slice(0, 32); // Ensure key is 32 bytes
  const messageWithNonce = decodeBase64(encryptedKeyB64);
  
  const nonce = messageWithNonce.slice(0, secretbox.nonceLength);
  const message = messageWithNonce.slice(secretbox.nonceLength);

  const decrypted = secretbox.open(message, nonce, key);

  return decrypted;
};

/**
 * Signs a message with a private key.
 * @param {string} message The message to sign.
 * @param {Uint8Array} secretKey The private key to sign with.
 * @returns {string} A base64 encoded signature.
 */
export const signMessage = (message: string, secretKey: Uint8Array): string => {
  const signature = sign.detached(decodeUTF8(message), secretKey);
  return encodeBase64(signature);
};
