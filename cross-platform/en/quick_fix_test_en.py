#!/usr/bin/env python3
"""
ModernSerialComm quick fix test.
Explicitly specify the correct configuration file.
"""

import asyncio
import sys

async def test_with_correct_config():
    """Test with the correct configuration file."""
    print("=== ModernSerialComm Fix Test ===")
    
    try:
        from modern_serial_comm import ModernSerialComm
        
        # Explicitly specify the configuration file for Linux
        comm = ModernSerialComm("serial_config_linux.ini")
        print("✅ Linux configuration file explicitly specified")
        
        # Verify the settings
        print(f"Configured port: {comm.port}")
        print(f"Configured baud rate: {comm.baudrate}")
        
        # Attempt to connect
        print("Trying to connect...")
        result = await comm.connect()
        
        if result:
            print("✅ Connection successful!")
            await comm.send_string("Fix test successful\n")
            print("✅ Send successful!")
            await comm.disconnect()
            print("✅ Disconnected successfully!")
            return True
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_with_manual_config():
    """Test with manual configuration."""
    print("\n=== Manual Configuration Test ===")
    
    try:
        from modern_serial_comm import ModernSerialComm, SerialConfig

        # Create configuration manually
        config = SerialConfig()
        config.config.set('SERIAL', 'port', '/dev/ttyS0')
        config.config.set('SERIAL', 'baudrate', '9600')
        config.config.set('SERIAL', 'timeout', '1.0')
        print("✅ Manual configuration created")

        # Create instance
        comm = ModernSerialComm()
        comm.config_manager = config  # Inject the configuration directly
        comm._load_settings_from_config()  # Reload settings

        print(f"Manual config port: {comm.port}")
        print(f"Manual config baud rate: {comm.baudrate}")

        # Attempt to connect
        print("Attempting connection with manual settings...")
        result = await comm.connect()

        if result:
            print("✅ Manual configuration connection successful!")
            await comm.send_string("Manual configuration test successful\n")
            print("✅ Manual configuration send successful!")
            await comm.disconnect()
            print("✅ Manual configuration disconnected successfully!")
            return True
        else:
            print("❌ Manual configuration connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Manual configuration error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main execution."""
    print("🔧 Starting ModernSerialComm fix test")
    print("=" * 50)
    
    # Event loop settings for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run tests
    config_test = await test_with_correct_config()
    manual_test = await test_with_manual_config()
    
    print("\n" + "=" * 50)
    print("📊 Fix Test Results")
    print(f"Configuration file specified: {'✅ Success' if config_test else '❌ Failure'}")
    print(f"Manual configuration: {'✅ Success' if manual_test else '❌ Failure'}")
    
    if config_test or manual_test:
        print("\n🎉 Fix successful! The dashboard should also work")
    else:
        print("\n❌ Further investigation is needed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
