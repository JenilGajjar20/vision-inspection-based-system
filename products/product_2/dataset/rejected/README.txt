Rejected images are kept here so they are not deleted, but they are also not
used for training or testing.

Use these folders when an image has a bad ROI, wrong camera angle, poor
lighting, blur, duplicate test data, or any other issue that would teach the
inspection model the wrong pattern.

Suggested workflow:
- Move bad OK training images to dataset/rejected/ok
- Move bad NOT OK training images to dataset/rejected/ng
- Move bad test images or duplicate test images to dataset/rejected/test
