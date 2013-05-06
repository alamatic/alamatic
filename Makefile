
CXX=g++
OBJ_DIR=obj
INCLUDE_DIR=include
BIN_DIR=bin
COMPILER_BIN=$(BIN_DIR)/alac
SOURCE_FILES=$(shell find src -type f -name '*.cpp')
HEADER_FILES=$(shell find $(INCLUDE_DIR) -type f -name '*.hpp')
OBJ_FILES=$(patsubst src/%.cpp,$(OBJ_DIR)/%.o,$(SOURCE_FILES))
CXX_OPTS := -std=gnu++0x

# This is where it ends up if you install the libgtest-dev Debian package.
# If you're not on Debian then you may wish to override this.
GTEST_ROOT=/usr/src/gtest

all: $(COMPILER_BIN)

$(COMPILER_BIN): $(BIN_DIR) $(OBJ_FILES)
	$(CXX) $(CXX_OPTS) -I$(INCLUDE_DIR) $(OBJ_FILES) -o $@

$(OBJ_DIR)/%.o: src/%.cpp $(OBJ_DIR) $(HEADER_FILES) Makefile
	@mkdir -p $(@D)
	$(CXX) -I$(INCLUDE_DIR) -O3 $(CXX_OPTS) -c $< -o $@

$(OBJ_DIR):
	[ -d $@ ] || mkdir -p $@

$(BIN_DIR):
	[ -d $@ ] || mkdir -p $@

tests.run: tests/*.cpp $(OBJ_FILES)
	@$(CXX) $(CXX_OPTS) -I$(GTEST_ROOT) -Itests -I$(INCLUDE_DIR) tests/*.cpp $(GTEST_ROOT)/src/gtest-all.cc $(GTEST_ROOT)/src/gtest_main.cc -lpthread -lgmock $(OBJ_FILES) -o tests.run

test: tests.run
	@./tests.run

show_config:
	@echo Header files are $(HEADER_FILES)
	@echo Source files are $(SOURCE_FILES)
	@echo Object files are $(OBJ_FILES)
	@echo Building with $(CXX) $(CXX_OPTS)
	@echo Will generate compiler binary at $(COMPILER_BIN)

.PHONY: all test show_config
