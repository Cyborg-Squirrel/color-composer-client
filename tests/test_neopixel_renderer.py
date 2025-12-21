"""Tests for NeoPixelRenderer class."""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock the board and neopixel modules before importing NeoPixelRenderer
sys.modules['board'] = MagicMock()
sys.modules['neopixel'] = MagicMock()

from color_composer_client.neopixel_config import NeoPixelConfig
from color_composer_client.neopixel_renderer import NeoPixelRenderer
from color_composer_client.rgb_frame import RgbFrame, RgbFrameOptions


@pytest.fixture
def mock_logger():
    """Fixture providing a mocked logger."""
    return Mock()


@pytest.fixture
def mock_neopixel():
    """Fixture providing a mocked NeoPixel object."""
    np = MagicMock()
    np.n = 30
    return np


@pytest.fixture
def renderer(mock_logger):
    """Fixture providing a NeoPixelRenderer instance."""
    return NeoPixelRenderer(mock_logger)


class TestNeoPixelRendererInitialization:
    """Tests for NeoPixelRenderer initialization."""

    def test_renderer_initialization(self, mock_logger):
        """Test creating a renderer instance."""
        renderer = NeoPixelRenderer(mock_logger)
        assert renderer.logger == mock_logger

    def test_renderer_has_empty_neopixels_dict(self, renderer):
        """Test that a new renderer has an empty neopixels dictionary."""
        assert len(renderer.neopixels) == 0

    def test_renderer_has_empty_buffer(self, renderer):
        """Test that a new renderer has an empty buffered frames list."""
        assert len(renderer.buffered_frames) == 0


@pytest.mark.usefixtures("mock_logger")
class TestNeoPixelRendererUpdateConfig:
    """Tests for updating NeoPixel configurations."""

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_update_single_config(self, mock_neopixel_class, mock_board, renderer):
        """Test updating a single NeoPixel configuration."""
        mock_neopixel_class.return_value = MagicMock()
        
        config = NeoPixelConfig("strip-1", "D10", 30, 75, "GRB")
        renderer.update_config(config)
        
        assert "D10" in renderer.neopixels

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_update_replaces_existing_config(self, mock_neopixel_class, mock_board, renderer):
        """Test that updating a config on the same pin replaces it."""
        mock_np = MagicMock()
        mock_neopixel_class.return_value = mock_np
        
        config1 = NeoPixelConfig("strip-1", "D10", 30, 75, "GRB")
        renderer.update_config(config1)
        
        config2 = NeoPixelConfig("strip-2", "D10", 50, 100, "RGB")
        renderer.update_config(config2)
        
        assert "D10" in renderer.neopixels
        mock_np.deinit.assert_called()


@pytest.mark.usefixtures("mock_logger")
class TestNeoPixelRendererUpdateConfigs:
    """Tests for updating multiple NeoPixel configurations at once."""

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_update_multiple_configs(self, mock_neopixel_class, mock_board, renderer):
        """Test updating multiple configurations."""
        mock_neopixel_class.return_value = MagicMock()
        
        configs = [
            NeoPixelConfig("strip-1", "D10", 30, 75, "GRB"),
            NeoPixelConfig("strip-2", "D12", 50, 100, "RGB"),
            NeoPixelConfig("strip-3", "D18", 100, 200, "BRG")
        ]
        
        renderer.update_configs(configs)
        
        assert "D10" in renderer.neopixels
        assert "D12" in renderer.neopixels
        assert "D18" in renderer.neopixels

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_update_configs_deinits_old_neopixels(self, mock_neopixel_class, mock_board, renderer):
        """Test that old NeoPixels are deinitialized when updating configs."""
        mock_np = MagicMock()
        mock_neopixel_class.return_value = mock_np
        
        old_config = NeoPixelConfig("old-strip", "D10", 30, 75, "GRB")
        renderer.update_config(old_config)
        
        new_configs = [
            NeoPixelConfig("new-strip-1", "D12", 50, 100, "RGB"),
            NeoPixelConfig("new-strip-2", "D18", 100, 200, "BRG")
        ]
        renderer.update_configs(new_configs)
        
        assert "D10" not in renderer.neopixels
        mock_np.deinit.assert_called()

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_update_configs_removes_orphaned_frames(self, mock_neopixel_class, mock_board, renderer):
        """Test that buffered frames for removed pins are deleted."""
        mock_neopixel_class.return_value = MagicMock()
        
        config1 = NeoPixelConfig("strip-1", "D10", 30, 75, "GRB")
        config2 = NeoPixelConfig("strip-2", "D12", 50, 100, "RGB")
        renderer.update_configs([config1, config2])
        
        options = RgbFrameOptions(clear_buffer=False)
        frame1 = RgbFrame("D10", 1000, options, [(255, 0, 0)])
        frame2 = RgbFrame("D12", 2000, options, [(0, 255, 0)])
        frame3 = RgbFrame("D18", 3000, options, [(0, 0, 255)])
        
        renderer.buffered_frames = [frame1, frame2, frame3]
        
        new_configs = [
            NeoPixelConfig("strip-1", "D10", 30, 75, "GRB"),
            NeoPixelConfig("strip-3", "D21", 100, 200, "BRG")
        ]
        renderer.update_configs(new_configs)
        
        pins_in_buffer = [f.pin for f in renderer.buffered_frames]
        assert "D12" not in pins_in_buffer
        assert "D18" not in pins_in_buffer


class TestNeoPixelRendererClearBuffer:
    """Tests for clearing buffered frames."""

    def test_clear_buffer_for_specific_pin(self, renderer):
        """Test clearing buffered frames for a specific pin."""
        options = RgbFrameOptions(clear_buffer=False)
        frame1 = RgbFrame("D10", 1000, options, [(255, 0, 0)])
        frame2 = RgbFrame("D12", 2000, options, [(0, 255, 0)])
        frame3 = RgbFrame("D10", 3000, options, [(0, 0, 255)])
        
        renderer.buffered_frames = [frame1, frame2, frame3]
        renderer.clear_buffer("D10")
        
        assert len(renderer.buffered_frames) == 1
        assert renderer.buffered_frames[0].pin == "D12"

    def test_clear_buffer_removes_all_matching_pins(self, renderer):
        """Test that all frames for a pin are removed."""
        options = RgbFrameOptions(clear_buffer=False)
        renderer.buffered_frames = [
            RgbFrame("D10", 1000, options, [(255, 0, 0)]),
            RgbFrame("D10", 2000, options, [(255, 0, 0)]),
            RgbFrame("D10", 3000, options, [(255, 0, 0)]),
        ]
        
        renderer.clear_buffer("D10")
        assert len(renderer.buffered_frames) == 0

    def test_clear_buffer_empty_buffer(self, renderer):
        """Test clearing buffer when it's already empty."""
        renderer.clear_buffer("D10")
        assert len(renderer.buffered_frames) == 0


class TestNeoPixelRendererQueue:
    """Tests for frame queuing operations."""

    def test_queue_empty_returns_true_when_empty(self, renderer):
        """Test that queue_empty returns True when buffer is empty."""
        renderer.buffered_frames.clear()
        assert renderer.queue_empty() is True

    def test_queue_empty_returns_false_when_not_empty(self, renderer):
        """Test that queue_empty returns False when buffer has frames."""
        renderer.buffered_frames.clear()
        options = RgbFrameOptions(clear_buffer=False)
        frame = RgbFrame("D10", 1000, options, [(255, 0, 0)])
        renderer.buffered_frames.append(frame)
        
        assert renderer.queue_empty() is False

    def test_queue_frame_adds_to_buffer(self, renderer):
        """Test that queue_frame adds a frame to the buffer."""
        renderer.buffered_frames.clear()
        options = RgbFrameOptions(clear_buffer=False)
        frame = RgbFrame("D10", 1000, options, [(255, 0, 0)])
        
        renderer.queue_frame(frame)
        
        assert len(renderer.buffered_frames) == 1
        assert renderer.buffered_frames[0] == frame

    def test_queue_frame_maintains_sorted_order(self, renderer):
        """Test that queued frames are sorted by timestamp."""
        renderer.buffered_frames.clear()
        options = RgbFrameOptions(clear_buffer=False)
        frame1 = RgbFrame("D10", 3000, options, [(255, 0, 0)])
        frame2 = RgbFrame("D10", 1000, options, [(0, 255, 0)])
        frame3 = RgbFrame("D10", 2000, options, [(0, 0, 255)])
        
        renderer.queue_frame(frame1)
        renderer.queue_frame(frame2)
        renderer.queue_frame(frame3)
        
        timestamps = [f.timestamp for f in renderer.buffered_frames]
        assert timestamps == [1000, 2000, 3000]


@pytest.mark.usefixtures("mock_logger")
class TestNeoPixelRendererRender:
    """Tests for rendering frames."""

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_render_frame(self, mock_neopixel_class, mock_board, renderer):
        """Test rendering a single frame to a NeoPixel strip."""
        mock_np = MagicMock()
        mock_np.n = 30
        mock_neopixel_class.return_value = mock_np
        renderer.neopixels["D10"] = mock_np
        
        options = RgbFrameOptions(clear_buffer=False)
        rgb_data = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        frame = RgbFrame("D10", 1000, options, rgb_data)
        
        renderer.render_frame(frame)
        
        assert mock_np.__setitem__.call_count >= 3
        mock_np.show.assert_called_once()

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_render_frame_respects_strip_size(self, mock_neopixel_class, mock_board, renderer):
        """Test that render_frame doesn't exceed strip LED count."""
        mock_np = MagicMock()
        mock_np.n = 5
        mock_neopixel_class.return_value = mock_np
        renderer.neopixels["D10"] = mock_np
        
        options = RgbFrameOptions(clear_buffer=False)
        # Data for 10 LEDs
        rgb_data = [(i, i, i) for i in range(10)]
        frame = RgbFrame("D10", 1000, options, rgb_data)
        
        renderer.render_frame(frame)
        
        assert mock_np.__setitem__.call_count == 5

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_render_queue_renders_ready_frames(self, mock_neopixel_class, mock_board, renderer):
        """Test that render_queue renders frames with current timestamp."""
        mock_np = MagicMock()
        mock_np.n = 30
        mock_neopixel_class.return_value = mock_np
        renderer.neopixels["D10"] = mock_np
        
        now = datetime.now()
        now_millis = int(now.timestamp() * 1000)
        
        options = RgbFrameOptions(clear_buffer=False)
        frame = RgbFrame("D10", now_millis, options, [(255, 0, 0)])
        renderer.buffered_frames.append(frame)
        
        renderer.render_queue()

        mock_np.show.assert_called()

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_render_queue_ignores_future_frames(self, mock_neopixel_class, mock_board, renderer):
        """Test that render_queue doesn't render frames with future timestamps."""
        mock_np = MagicMock()
        mock_np.n = 30
        mock_neopixel_class.return_value = mock_np
        renderer.neopixels["D10"] = mock_np
        
        future_time = datetime.now() + timedelta(seconds=5)
        future_millis = int(future_time.timestamp() * 1000)
        
        options = RgbFrameOptions(clear_buffer=False)
        frame = RgbFrame("D10", future_millis, options, [(255, 0, 0)])
        renderer.buffered_frames.append(frame)
        
        renderer.render_queue()
        
        assert len(renderer.buffered_frames) == 1

    @patch('color_composer_client.neopixel_renderer.board')
    @patch('color_composer_client.neopixel_renderer.neopixel.NeoPixel')
    def test_set_brightness(self, mock_neopixel_class, mock_board, renderer):
        """Test setting the brightness of the strip."""
        mock_np = MagicMock()
        mock_neopixel_class.return_value = mock_np
        renderer.neopixels["D10"] = mock_np
        
        options = RgbFrameOptions(clear_buffer=False)
        renderer.set_brightness("D10", 50)

        assert mock_np.brightness == 0.5