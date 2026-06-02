package com.example.profile;

public class UserProfileController {
    public UserProfileResponse getProfile(User user) {
        return new UserProfileResponse(
                user.getName(),
                user.getMobile(),
                user.getEmail(),
                user.getCardNo());
    }
}
