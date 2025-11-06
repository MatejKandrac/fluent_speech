"""
Simple test script for the Video Analysis API.
"""
import requests
import json
import sys


BASE_URL = "http://localhost:8001/api"


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_analyze_video(video_id):
    """Test video analysis endpoint."""
    print(f"\nTesting video analysis for video ID: {video_id}...")
    response = requests.post(f"{BASE_URL}/analyze/video/{video_id}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        analysis_id = response.json().get('analysis_id')
        print(f"\n✅ Analysis completed! Analysis ID: {analysis_id}")
        return analysis_id
    else:
        print(f"\n❌ Analysis failed!")
        return None


def test_get_analysis(analysis_id):
    """Test get analysis endpoint."""
    print(f"\nGetting analysis results for ID: {analysis_id}...")
    response = requests.get(f"{BASE_URL}/analysis/{analysis_id}/")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if 'analysis' in data:
            analysis = data['analysis']
            print(f"Total frames: {analysis.get('total_frames', 0)}")
            print(f"Created at: {analysis.get('created_at')}")
            print(f"Number of frame data: {len(analysis.get('data', []))}")

            # Print first frame landmarks as sample
            if analysis.get('data'):
                first_frame = analysis['data'][0]
                print(f"\nFirst frame timestamp: {first_frame.get('timestamp')}")
                print(f"Number of landmarks: {len(first_frame.get('landmarks', {}))}")
                print("\nSample landmarks (first 3):")
                for i, (name, landmark) in enumerate(first_frame.get('landmarks', {}).items()):
                    if i >= 3:
                        break
                    print(f"  {name}: x={landmark['x']:.3f}, y={landmark['y']:.3f}, z={landmark['z']:.3f}, visibility={landmark['visibility']:.3f}")
        return True
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("Video Analysis Microservice - API Test")
    print("=" * 60)

    # Test health check
    if not test_health_check():
        print("\n❌ Health check failed! Is the service running?")
        sys.exit(1)

    print("\n✅ Health check passed!")

    # Test video analysis
    if len(sys.argv) < 2:
        print("\nUsage: python test_api.py <video_id>")
        print("Example: python test_api.py 507f1f77bcf86cd799439011")
        sys.exit(1)

    video_id = sys.argv[1]
    analysis_id = test_analyze_video(video_id)

    if analysis_id:
        # Test get analysis
        test_get_analysis(analysis_id)

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
