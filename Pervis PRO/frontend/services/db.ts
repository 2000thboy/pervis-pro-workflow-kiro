// IndexedDB Wrapper for Large File Storage & Vector Store
// Database Version: 1
const DB_NAME = 'PreVisProDB';
const STORE_FILES = 'files'; // Stores raw Blobs
const STORE_VECTORS = 'vectors'; // Stores Embeddings { id, embedding, metadata }

export interface StoredFile {
  id: string;
  blob: Blob;
  mimeType: string;
  filename: string;
  createdAt: number;
}

export interface StoredVector {
  id: string; // Corresponds to Asset ID
  vector: number[];
  text: string; // The text that was embedded (for debug)
}

class LocalDB {
  private dbPromise: Promise<IDBDatabase>;

  constructor() {
    this.dbPromise = this.openDB();
  }

  private openDB(): Promise<IDBDatabase> {
      return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_FILES)) {
          db.createObjectStore(STORE_FILES, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(STORE_VECTORS)) {
          db.createObjectStore(STORE_VECTORS, { keyPath: 'id' });
        }
      };

      request.onsuccess = (event) => resolve((event.target as IDBOpenDBRequest).result);
      request.onerror = (event) => reject((event.target as IDBOpenDBRequest).error);
    });
  }
  
  // Public method to force initialization check
  async init(): Promise<void> {
      await this.dbPromise;
  }

  // --- File Operations ---

  async saveFile(file: StoredFile): Promise<void> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_FILES, 'readwrite');
      tx.objectStore(STORE_FILES).put(file);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async getFile(id: string): Promise<StoredFile | undefined> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_FILES, 'readonly');
      const request = tx.objectStore(STORE_FILES).get(id);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async deleteFile(id: string): Promise<void> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_FILES, 'readwrite');
      tx.objectStore(STORE_FILES).delete(id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  // --- Vector Operations ---

  async saveVector(data: StoredVector): Promise<void> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_VECTORS, 'readwrite');
      tx.objectStore(STORE_VECTORS).put(data);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async deleteVector(id: string): Promise<void> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_VECTORS, 'readwrite');
        tx.objectStore(STORE_VECTORS).delete(id);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
    });
  }

  async getAllVectors(): Promise<StoredVector[]> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_VECTORS, 'readonly');
      const request = tx.objectStore(STORE_VECTORS).getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
}

export const db = new LocalDB();

// Explicit export for bootstrap usage
export const initDB = async () => {
    return db.init();
};