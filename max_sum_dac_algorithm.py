### HOW TO USE: Import & instantiate class, call max_subarray method with list parameter, retrieve indices attributes

class MSSDAC:
    """Implements Maximum-Subarray-Sum Divide & Conquer algorithm to output highest contiguous sum & indices."""

    def __init__(self):
        self.left_index = 0
        self.right_index = 0

    def max_subarray(self, input_list, low=0, high=None):
        """Recursively implements DAC algorithm to find contiguous sub-array whose sum is the largest."""

        if high is None:
            high = len(input_list) - 1

        # Establish base case for when low and high values are equal
        if low == high:
            if input_list[low] > 0:
                return input_list[low]
            else:
                return 0

        # Divide
        mid = (low + high) // 2

        # Conquer
        max_left = self.max_subarray(input_list, low, mid)
        max_right = self.max_subarray(input_list, mid + 1, high)

        # Combine
        max_left2_center = left2_center = 0
        for i in range(mid, low - 1, -1):
            left2_center += input_list[i]
            if left2_center > max_left2_center:
                self.left_index = i
            max_left2_center = max(left2_center, max_left2_center)

        max_right2_center = right2_center = 0
        for i in range(mid + 1, high + 1):
            right2_center += input_list[i]
            if right2_center > max_right2_center:
                self.right_index = i
            max_right2_center = max(right2_center, max_right2_center)

        return max(max_left, max_right, max_left2_center + max_right2_center)
