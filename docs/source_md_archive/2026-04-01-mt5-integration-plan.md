# MT5 Integration Plan - 2026-04-01

## Project Goal
Integrate MetaTrader 5 (MT5) to serve as the primary source for live market data and as the execution broker for live trading operations within the bot.

---

## Analysis of Existing Code & Reuse

A review of the current codebase reveals a modular architecture that is well-suited for extension. No direct code can be reused, but the following architectural patterns and base classes are critical for this integration and will be leveraged to avoid duplication:

-   **Broker Interface**: The `execution/base_broker.py` file defines an abstract class `BaseBroker`. The new `MT5Broker` **must** inherit from this class and implement all its abstract methods (`connect`, `place_order`, etc.). This ensures compatibility with the existing trading logic.
-   **Broker Template**: The `execution/paper_broker.py` provides a complete, concrete implementation of `BaseBroker` and serves as an excellent structural template for the new `MT5Broker`.
-   **Data Feed Pattern**: Data provider classes, such as `data/alpha_vantage_feed.py`, establish a clear pattern for fetching data and returning it as a pandas DataFrame. The new `MT5Feed` will follow this pattern.
-   **Data Factory**: The `data/factory.py` shows how data providers are selected via configuration. This pattern will be used for both the data feed and the broker.
-   **Irrelevant Folders**: The `RND/scripts/` folder does not contain any logic that can be reused for this integration.

## Integration Strategy

The integration will be executed in phases to ensure modularity and testability.

### Phase 1: Environment & Configuration

1.  **Install MT5 Library**: Add `MetaTrader5` to the `requirements.txt` file.

2.  **Update Configuration**:
    *   **Environment Settings**: Update `config/settings.example.env` with MT5-specific variables:
      ```
      MT5_ACCOUNT="<your_account_number>"
      MT5_PASSWORD="<your_password>"
      MT5_SERVER="<your_broker_server>"
      MT5_TERMINAL_PATH="<path_to_terminal64.exe>"
      BROKER_PROVIDER="paper" # Add this to select paper or mt5
      ```
    *   **Config Loading**: Update `config/config.py` to load the new variables.

### Phase 2: Data Feed Integration

1.  **Create MT5 Data Feed Component**:
    *   Create `data/mt5_feed.py`.
    *   The `MT5Feed` class will connect to MT5 and implement a `get_candlesticks` method, following the pattern set by `AlphaVantageFeed` and returning a pandas DataFrame.

2.  **Update Data Factory**:
    *   Modify `data/factory.py` to recognize and instantiate `MT5Feed` when `MARKET_DATA_PROVIDER` is set to `'mt5'`.

### Phase 3: Execution Broker Integration

1.  **Create MT5 Broker Component**:
    *   Create `execution/mt5_broker.py`.
    *   The `MT5Broker` class will inherit from `execution.base_broker.BaseBroker`.
    *   It will implement all abstract methods, using `execution.paper_broker.PaperBroker` as a structural guide. Calls to the `MetaTrader5` library will replace the simulation logic.

2.  **Create Broker Factory & Update Main Logic**:
    *   Create a new file `execution/broker_factory.py`.
    *   Inside, create a `create_broker()` function that reads the `BROKER_PROVIDER` config variable and returns an instance of either `PaperBroker` or `MT5Broker`.
    *   Update `main.py` to use this new factory to instantiate the broker, ensuring a clean separation of concerns.

### Phase 4: Testing

1.  **Create Integration Tests**:
    *   Create a new test file, `tests/test_mt5_integration.py`.
    *   Write tests to validate the complete workflow with a running MT5 terminal instance.

---

This documentation outlines the complete plan for integrating MT5 into the trading bot, ensuring that the new functionality aligns with the existing modular architecture.
