#!/usr/bin/env python3
"""
Asynchronous serial connection debugging tool
Identify issues with ModernSerialComm
"""

import asyncio
import sys
import os

def test_sync_serial():
    """Synchronous serial connection test"""
    print("=== Synchronous serial connection test ===")
    
    try:
        import serial
        print(f"✅ pyserial version: {serial.VERSION}")
        
        with serial.Serial('/dev/ttyS0', 9600, timeout=1) as ser:
            print("✅ Synchronous connection successful")
            ser.write(b'sync test\n')
            print("✅ Synchronous send successful")
            return True
            
    except Exception as e:
        print(f"❌ Synchronous connection failed: {e}")
        return False

async def test_async_serial():
    """Asynchronous serial connection test"""
    print("\n=== Asynchronous serial connection test ===")
    
    try:
        import serial_asyncio
        print("✅ serial_asyncio imported")
        
        # Basic asynchronous connection
        print("Attempting asynchronous connection...")
        reader, writer = await serial_asyncio.open_serial_connection(
            url='/dev/ttyS0',
            baudrate=9600,
            timeout=1.0
        )
        print("✅ Asynchronous connection successful")
        
        # Send test
        writer.write(b'async test\n')
        await writer.drain()
        print("✅ Asynchronous send successful")
        
        # Cleanup
        writer.close()
        if hasattr(writer, 'wait_closed'):
            await writer.wait_closed()
        print("✅ Asynchronous disconnect successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Asynchronous connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_modern_serial_comm():
    """ModernSerialComm test"""
    print("\n=== ModernSerialComm test ===")
    
    try:
        # Adjust path
        sys.path.append('.')
        from modern_serial_comm import ModernSerialComm, SerialConfig
        print("✅ ModernSerialComm imported")
        
        # Create configuration
        config = SerialConfig()
        config.config.set('SERIAL', 'port', '/dev/ttyS0')
        config.config.set('SERIAL', 'baudrate', '9600')
        print("✅ Config created")
        
        # Create instance
        comm = ModernSerialComm()
        comm.config = config  # direct assignment
        print("✅ ModernSerialComm instance created")
        
        # Connection attempt
        print("Attempting ModernSerialComm connection...")
        result = await comm.connect()
        
        if result:
            print("✅ ModernSerialComm connection successful")
            await comm.send_string("ModernSerialComm test\n")
            print("✅ ModernSerialComm send successful")
            await comm.disconnect()
            print("✅ ModernSerialComm disconnect successful")
            return True
        else:
            print("❌ ModernSerialComm connection failed")
            return False
            
    except Exception as e:
        print(f"❌ ModernSerialComm exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config_file():
    """Check configuration files"""
    print("\n=== Checking configuration files ===")
    
    config_files = [
        'serial_config_linux.ini',
        'serial_config.ini'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file} exists")
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                print(f"Content:\n{content}")
            except Exception as e:
                print(f"❌ Read error: {e}")
        else:
            print(f"❌ {config_file} does not exist")

def check_permissions():
    """Permission check"""
    print("\n=== Checking permissions ===")
    
    device = '/dev/ttyS0'
    try:
        # Read permission
        readable = os.access(device, os.R_OK)
        writable = os.access(device, os.W_OK)
        print(f"Read permission: {readable}")
        print(f"Write permission: {writable}")
        
        # File status
        stat_info = os.stat(device)
        print(f"File mode: {oct(stat_info.st_mode)}")
        
    except Exception as e:
        print(f"❌ Permission check error: {e}")

async def main():
    """Main execution"""
    print("🔍 Starting asynchronous serial debug")
    print("=" * 50)
    
    # Event loop setup for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    check_permissions()
    check_config_file()
    
    # Run tests
    sync_ok = test_sync_serial()
    async_ok = await test_async_serial()
    modern_ok = await test_modern_serial_comm()
    
    print("\n" + "=" * 50)
    print("📊 Test summary")
    print(f"Synchronous serial: {'✅ Success' if sync_ok else '❌ Failure'}")
    print(f"Asynchronous serial: {'✅ Success' if async_ok else '❌ Failure'}")
    print(f"ModernSerialComm: {'✅ Success' if modern_ok else '❌ Failure'}")
    
    if sync_ok and not async_ok:
        print("\n💡 Diagnosis: There is an issue with the async library")
        print("   Solution: Check or downgrade pyserial-asyncio version")
    elif sync_ok and async_ok and not modern_ok:
        print("\n💡 Diagnosis: There is an issue with the ModernSerialComm configuration")
        print("   Solution: Review configuration file or code")
    elif not sync_ok:
        print("\n💡 Diagnosis: There is a problem with the basic serial connection")
        print("   Solution: Check permissions or device")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
