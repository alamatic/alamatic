
def optimize_terminator(block):
    terminator = block.terminator
    new_terminator = terminator.get_optimal_equivalent(terminator)
    if new_terminator is not terminator:
        block.terminator = new_terminator
        return True
    else:
        return False
