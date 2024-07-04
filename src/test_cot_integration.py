import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from getTarget import resolveTarget

class MockSocket:
    def __init__(self):
        self.sent_messages = []
        self.closed = False

    def sendto(self, message, address):
        if self.closed:
            raise Exception("Cannot send on a closed socket")
        self.sent_messages.append((message, address))

    def close(self):
        self.closed = True

class TestIntegration(unittest.TestCase):

    @patch('cursor_on_target.setup_multicast_socket')
    def test_resolve_target_and_send_cot(self, mock_setup_socket):
        # Create a mock socket
        mock_socket = MockSocket()
        mock_setup_socket.return_value = mock_socket

        # Sample input data
        y, x, z = 40.7128, -74.0060, 100  # New York City coordinates and altitude
        azimuth, theta = 45, 89  # Camera is looking nearly straight down
        
        # Mock elevation data and parameters
        elevationData = [[0, 10, 20], [5, 15, 25], [10, 20, 30]]
        xParams = (-74.01, -74.00, 0.005, 3)
        yParams = (40.72, 40.71, -0.005, 3)

        # Run resolveTarget
        result = resolveTarget(y, x, z, azimuth, theta, elevationData, xParams, yParams)

        # Check if resolveTarget returned a valid result
        self.assertIsNotNone(result)
        finalDist, tarY, tarX, tarZ, terrainAlt = result

        # Check if a CoT message was sent
        self.assertEqual(len(mock_socket.sent_messages), 1)
        sent_message, address = mock_socket.sent_messages[0]

        # Parse the sent XML message
        root = ET.fromstring(sent_message.decode('utf-8'))

        # Verify the content of the CoT message
        point = root.find('point')
        self.assertAlmostEqual(float(point.get('lon')), float(tarY), places=6)
        self.assertAlmostEqual(float(point.get('lat')), float(tarX), places=6)
        self.assertAlmostEqual(float(point.get('hae')), float(tarZ), places=2)

        # Verify other aspects of the CoT message
        self.assertEqual(root.get('type'), 'a-p-G')
        self.assertEqual(root.get('how'), 'h-c')

        # Verify the multicast address and port
        self.assertEqual(address, ('239.2.3.1', 6969))

        # Verify that the socket was closed
        self.assertTrue(mock_socket.closed, "Socket was not closed after sending the message")

if __name__ == '__main__':
    unittest.main()