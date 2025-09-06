import os
import json
import hashlib
from cryptography.fernet import Fernet

def split_and_encrypt(original_filename: str, data: bytes, pieces: int) -> dict:
    """
    Encrypts data, splits it into pieces, and returns a dictionary of file parts
    including the manifest and encryption key.
    
    Args:
        original_filename: The original name of the file being split.
        data: The byte content of the file.
        pieces: The number of chunks to split the encrypted data into.

    Returns:
        A dictionary where keys are filenames and values are the byte content for each part.
    """
    # 1. Generate a unique encryption key and initialize Fernet
    key = Fernet.generate_key()
    fernet = Fernet(key)

    # 2. Encrypt the data
    encrypted_data = fernet.encrypt(data)

    # 3. Calculate chunk sizes
    file_size = len(encrypted_data)
    if file_size < pieces:
        raise ValueError("File size is smaller than the number of pieces requested.")
    
    chunk_size = file_size // pieces
    remainder = file_size % pieces

    # 4. Prepare the manifest and the dictionary for the final files
    manifest = {
        'original_filename': original_filename,
        'chunk_order': [],
        'chunk_hashes': []
    }
    output_files = {}
    
    # Add the encryption key to the output files
    output_files['encryption_key.key'] = key
    
    # 5. Create chunks and populate the manifest
    current_pos = 0
    for i in range(pieces):
        # The last piece gets the remainder
        current_chunk_size = chunk_size
        if i == pieces - 1:
            current_chunk_size += remainder
        
        chunk_data = encrypted_data[current_pos : current_pos + current_chunk_size]
        current_pos += current_chunk_size
        
        chunk_hash = hashlib.sha256(chunk_data).hexdigest()
        chunk_filename = f"chunk_{i+1}.bin"

        manifest['chunk_order'].append(chunk_filename)
        manifest['chunk_hashes'].append({'filename': chunk_filename, 'hash': chunk_hash})
        
        output_files[chunk_filename] = chunk_data

    # 6. Add the finalized manifest to the output files
    manifest_bytes = json.dumps(manifest, indent=4).encode('utf-8')
    output_files['manifest.json'] = manifest_bytes

    return output_files


def join_and_decrypt(file_data: dict) -> tuple[str, bytes]:
    """
    Reassembles encrypted chunks, verifies their integrity, decrypts them,
    and returns the original filename and data.

    Args:
        file_data: A dictionary where keys are filenames and values are the byte content
                   of the manifest, key, and all chunks.

    Returns:
        A tuple containing the original filename (str) and the decrypted data (bytes).
    """
    # 1. Extract the key, manifest, and chunks from the provided files
    key = file_data.get('encryption_key.key')
    manifest_data = file_data.get('manifest.json')

    if not key or not manifest_data:
        raise ValueError("Missing encryption_key.key or manifest.json.")

    manifest = json.loads(manifest_data)
    original_filename = manifest['original_filename']
    
    # 2. Verify and reassemble the encrypted data
    encrypted_data = b''
    for i, chunk_filename in enumerate(manifest['chunk_order']):
        chunk_data = file_data.get(chunk_filename)
        if not chunk_data:
            raise ValueError(f"Missing chunk file: {chunk_filename}")

        # Verify integrity
        expected_hash = manifest['chunk_hashes'][i]['hash']
        actual_hash = hashlib.sha256(chunk_data).hexdigest()
        if expected_hash != actual_hash:
            raise ValueError(f"Hash mismatch for chunk {chunk_filename}. File may be corrupt.")
        
        encrypted_data += chunk_data
    
    # 3. Decrypt the data
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)

    return original_filename, decrypted_data

