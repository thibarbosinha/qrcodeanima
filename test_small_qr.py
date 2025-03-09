import segno

def create_small_qr(scale=5):
    qr = segno.make('https://www.sicredi.com.br/coop/grandesrios/assembleias-2025/', error='h')
    
    # Try different sizes with transparency
    qr.to_artistic(
        background='sicre.gif',
        target=f'qr_transparent_{scale}.gif',
        scale=scale,
        dark='#33333366',  # Semi-transparent dark modules
        finder_dark='#333333',  # Solid dark for finder patterns
        finder_light='#FFFFFF'  # Solid white for finder patterns
    )

if __name__ == "__main__":
    # Test with different scales and transparency
    for scale in [15, 20, 25]:
        print(f"Creating transparent QR with scale {scale}...")
        create_small_qr(scale)