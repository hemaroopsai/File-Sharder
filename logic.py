import os
import json
import hashlib
from cryptography.fernet import Fernet
from pathlib import Path

def split_and_encrypt(original_filename: str, data: bytes, pieces: int, temp_dir: Path):
    """
    Encrypts data and writes the output files (chunks, key, manifest)
    to a temporary directory on disk instead of returning them in memory.
    """
    if len(data) < pieces:
        raise ValueError("File size is smaller than the number of pieces requested.")

    # 1. Generate key and encrypt data
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)
    
    # 2. Prepare for chunking
    file_size = len(encrypted_data)
    chunk_size = file_size // pieces
    remainder = file_size % pieces

    manifest = {
        'original_filename': original_filename,
        'chunk_order': [],
        'chunk_hashes': []
    }
    
    # NEW: Write the key file directly to the temporary directory
    (temp_dir / 'encryption_key.key').write_bytes(key)

    # 3. Create chunks and write them to disk
    current_pos = 0
    for i in range(pieces):
        current_chunk_size = chunk_size
        if i == pieces - 1:
            current_chunk_size += remainder
        
        chunk_data = encrypted_data[current_pos : current_pos + current_chunk_size]
        current_pos += current_chunk_size
        
        chunk_hash = hashlib.sha256(chunk_data).hexdigest()
        chunk_filename = f"chunk_{i+1}.bin"

        manifest['chunk_order'].append(chunk_filename)
        manifest['chunk_hashes'].append({'filename': chunk_filename, 'hash': chunk_hash})
        
        # NEW: Write each chunk directly to a file
        (temp_dir / chunk_filename).write_bytes(chunk_data)

    # 4. Finalize and write the manifest file to disk
    manifest_bytes = json.dumps(manifest, indent=4).encode('utf-8')
    (temp_dir / 'manifest.json').write_bytes(manifest_bytes)

def join_and_decrypt(file_data: dict[str, bytes]):
    """
    Reassembles and decrypts a file from its manifest, key, and chunk data.
    """
    # 1. Extract the necessary files from the provided dictionary
    try:
        manifest_data = json.loads(file_data['manifest.json'])
        key = file_data['encryption_key.key']
        
        # Create a mapping of chunk filenames to their hashes for easy lookup
        hash_map = {item['filename']: item['hash'] for item in manifest_data['chunk_hashes']}
    except KeyError as e:
        raise ValueError(f"Missing required file for joining: {e}")

    # 2. Initialize the decryption engine
    fernet = Fernet(key)
    
    # 3. Verify and reassemble chunks in the correct order
    reassembled_encrypted_data = bytearray()
    for chunk_filename in manifest_data['chunk_order']:
        chunk_data = file_data.get(chunk_filename)
        if not chunk_data:
            raise ValueError(f"Missing chunk file: {chunk_filename}")
        
        # Verify the integrity of the chunk
        expected_hash = hash_map.get(chunk_filename)
        actual_hash = hashlib.sha256(chunk_data).hexdigest()
        
        if actual_hash != expected_hash:
            raise ValueError(f"Chunk integrity check failed for {chunk_filename}. The file may be corrupted.")
            
        reassembled_encrypted_data.extend(chunk_data)
        
    # 4. Decrypt the reassembled data
    decrypted_data = fernet.decrypt(reassembled_encrypted_data)
    
    # 5. Return the original filename and the decrypted data
    original_filename = manifest_data.get('original_filename', 'recovered_file')
    
    return original_filename, decrypted_data

